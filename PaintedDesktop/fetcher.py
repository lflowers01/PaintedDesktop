"""Art sources: Art Institute of Chicago, Rijksmuseum and Wikimedia Commons.

Each fetcher yields candidate paintings for a style (landscape / seascape / veduta)
and downloads one at exactly the size the screen needs.
"""

import html
import logging
import math
import random
import re
from io import BytesIO
from pathlib import Path
from typing import Dict, Iterator, Optional, Tuple

import requests
from PIL import Image

logger = logging.getLogger(__name__)

# (connect, read) seconds. Without a timeout a stalled connection blocks the app forever.
TIMEOUT = (10, 60)
APP_UA = "PaintedDesktop (https://github.com/lflowers01/PaintedDesktop)"
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")


def target_size(width, height, screen: Tuple[int, int], mode: str = "fill") -> Optional[Tuple[int, int]]:
    """Pixel size to download so the image covers ("fill") or fits inside ("fit") the
    screen without upscaling. None if the original is too small or the wrong shape."""
    sw, sh = screen
    if not (width and height and sw and sh):
        return None
    # ponytail: fixed aspect window; tall portraits would be mostly cropped (fill) or mostly bars (fit)
    if not 0.6 <= (width / height) / (sw / sh) <= 1.7:
        return None
    scale = max(sw / width, sh / height) if mode == "fill" else min(sw / width, sh / height)
    if scale > 1.01:
        return None
    return math.ceil(width * scale), math.ceil(height * scale)


def _strip_html(text: str) -> str:
    # Commons hides machine-readable Wikidata markup in display:none elements; drop it with its text
    text = re.sub(r'<(\w+)[^>]*display:\s*none[^>]*>.*?</\1>', " ", text or "", flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", text).strip()[:150]


def _save_image(data: bytes, path: Path, screen, mode) -> Optional[str]:
    """Validate a downloaded image and write it to path as JPEG. Returns the path or None."""
    img = Image.open(BytesIO(data))
    if target_size(*img.size, screen, mode) is None:
        logger.info(f"Rejected {path.name}: downloaded size {img.size} is too small for {screen}")
        return None
    tmp = path.with_suffix(".tmp")
    if img.format == "JPEG":
        tmp.write_bytes(data)
    else:
        img.convert("RGB").save(tmp, "JPEG", quality=95)
    tmp.replace(path)  # atomic, so a crash never leaves a half-written wallpaper
    return str(path)


class Fetcher:
    """Base class: subclasses implement _search, _image_url and optionally _resolve."""

    NAME = ""
    SOURCE = ""
    USER_AGENT = APP_UA

    def __init__(self, screen: Tuple[int, int], mode: str = "fill"):
        self.screen = screen
        self.mode = mode
        self.session = requests.Session()
        self.session.headers["User-Agent"] = self.USER_AGENT

    def _get_json(self, url: str, **kwargs):
        response = self.session.get(url, timeout=TIMEOUT, **kwargs)
        response.raise_for_status()
        return response.json()

    def _painting(self, **fields) -> Dict:
        return {"source": self.SOURCE, "institution": self.NAME, "title": "Untitled",
                "artist": "Unknown artist", "year": "", "source_url": "",
                "width": None, "height": None, **fields}

    def candidates(self, style: str) -> Iterator[Dict]:
        """Yield paintings for a style. Network errors end the iteration instead of raising,
        and paintings whose known size can't fill the screen are skipped for free."""
        try:
            for painting in self._search(style):
                if painting["width"] and target_size(painting["width"], painting["height"],
                                                     self.screen, self.mode) is None:
                    continue
                yield painting
        except Exception as e:
            logger.warning(f"{self.NAME} search failed ({style}): {e}")

    def fetch_image(self, painting: Dict, cache_dir: Path) -> Optional[str]:
        """Download the painting sized for the screen into cache_dir. Returns the path or None."""
        try:
            if not painting["width"] and not self._resolve(painting):
                return None
            size = target_size(painting["width"], painting["height"], self.screen, self.mode)
            if size is None:
                logger.debug(f"Skipping {painting['id']}: {painting['width']}x{painting['height']} doesn't suit {self.screen}")
                return None
            painting["image_url"] = self._image_url(painting, size)
            response = self.session.get(painting["image_url"], timeout=TIMEOUT)
            response.raise_for_status()
            name = re.sub(r"[^\w.-]", "_", f"{self.SOURCE}_{painting['id']}")[:120] + ".jpg"
            return _save_image(response.content, Path(cache_dir) / name, self.screen, self.mode)
        except Exception as e:
            logger.warning(f"{self.NAME} image fetch failed for {painting.get('id')}: {e}")
            return None

    def _search(self, style: str) -> Iterator[Dict]:
        raise NotImplementedError

    def _resolve(self, painting: Dict) -> bool:
        """Fill in size and metadata the search didn't provide."""
        return False

    def _image_url(self, painting: Dict, size: Tuple[int, int]) -> str:
        raise NotImplementedError


class ARTICFetcher(Fetcher):
    NAME = "Art Institute of Chicago"
    SOURCE = "artic"
    USER_AGENT = BROWSER_UA  # www.artic.edu's image CDN answers 403 to non-browser agents
    API = "https://api.artic.edu/api/v1/artworks/search"
    SUBJECTS = {
        "landscape": ["landscapes"],
        "seascape": ["seascapes", "coastal scenes", "marine art"],
        "veduta": ["cityscapes"],
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session.headers["AIC-User-Agent"] = APP_UA  # AIC asks API clients to identify themselves

    def _page(self, style: str, page: int) -> Dict:
        query = {"bool": {
            "must": [
                {"term": {"is_public_domain": True}},
                {"exists": {"field": "image_id"}},
                {"match_phrase": {"medium_display": "oil on"}},
            ],
            "should": [{"match_phrase": {"subject_titles": s}} for s in self.SUBJECTS.get(style, [style])],
            "minimum_should_match": 1,
        }}
        payload = {"query": query, "limit": 100, "page": page,
                   "fields": ["id", "title", "image_id", "artist_display", "date_display", "thumbnail"]}
        response = self.session.post(self.API, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()

    def _search(self, style):
        first = self._page(style, 1)
        pages = list(range(1, first.get("pagination", {}).get("total_pages", 1) + 1))
        random.shuffle(pages)  # every page gets a fair turn, not just the top results
        for page in pages:
            items = (first if page == 1 else self._page(style, page)).get("data", [])
            random.shuffle(items)
            for art in items:
                thumb = art.get("thumbnail") or {}
                artist = (art.get("artist_display") or "").split("\n")
                yield self._painting(
                    id=str(art["id"]),
                    image_id=art["image_id"],
                    title=art.get("title") or "Untitled",
                    artist=f"{artist[0]} ({artist[1]})" if len(artist) > 1 else artist[0] or "Unknown artist",
                    year=art.get("date_display") or "",
                    source_url=f"https://www.artic.edu/artworks/{art['id']}",
                    width=thumb.get("width"),
                    height=thumb.get("height"),
                )

    def _image_url(self, painting, size):
        # "full" and "max" sizes are blocked; explicit pixel widths are allowed
        return f"https://www.artic.edu/iiif/2/{painting['image_id']}/full/{size[0]},/0/default.jpg"


class RijksmuseumFetcher(Fetcher):
    NAME = "Rijksmuseum"
    SOURCE = "rijksmuseum"
    API = "https://data.rijksmuseum.nl/search/collection"
    ENGLISH = "http://vocab.getty.edu/aat/300388277"
    # The Linked Art search has no genre field; Dutch title words are the most reliable proxy.
    QUERIES = {
        "landscape": [{"title": "landschap"}],
        "seascape": [{"title": "zee"}, {"title": "strand"}],
        "veduta": [{"title": "gezicht op"}],
    }

    def _ld(self, url: str) -> Dict:
        return self._get_json(url, headers={"Accept": "application/ld+json"})

    def _search(self, style):
        for query in self.QUERIES.get(style, [{"title": style}]):
            url = self.API
            params = {"type": "painting", "material": "oil paint", "imageAvailable": "true", **query}
            while url:
                data = self._get_json(url, params=params)
                items = data.get("orderedItems", [])
                random.shuffle(items)
                for item in items:
                    yield self._painting(id=item["id"].rsplit("/", 1)[-1], object_url=item["id"])
                url, params = (data.get("next") or {}).get("id"), None  # next URL carries the query

    def _english_or_first(self, names) -> str:
        names = [n for n in names or [] if n.get("content")]
        english = [n for n in names if any(l.get("id") == self.ENGLISH for l in n.get("language", []))]
        return (english or names or [{}])[0].get("content", "")

    def _resolve(self, painting):
        obj = self._ld(painting["object_url"])
        production = obj.get("produced_by", {})
        painting["title"] = self._english_or_first(
            [n for n in obj.get("identified_by", []) if n.get("type") == "Name"]) or "Untitled"
        painting["artist"] = self._english_or_first(production.get("referred_to_by")) or "Unknown artist"
        painting["year"] = self._english_or_first(production.get("timespan", {}).get("identified_by"))
        for text in obj.get("subject_of", []):
            for carrier in text.get("digitally_carried_by", []):
                for point in carrier.get("access_point", []):
                    if "rijksmuseum.nl" in point.get("id", ""):
                        painting["source_url"] = point["id"].replace("/nl/collectie/", "/en/collection/")
        painting["source_url"] = painting["source_url"] or painting["object_url"]

        # Object -> VisualItem -> DigitalObject -> IIIF image service (Micrio)
        visual = self._ld(obj["shows"][0]["id"])
        digital = self._ld(visual["digitally_shown_by"][0]["id"])
        painting["iiif"] = digital["access_point"][0]["id"].split("/full/")[0]
        info = self._get_json(painting["iiif"] + "/info.json")
        painting["width"], painting["height"] = info["width"], info["height"]
        return True

    def _image_url(self, painting, size):
        return f"{painting['iiif']}/full/{size[0]},/0/default.jpg"


class WikimediaFetcher(Fetcher):
    NAME = "Wikimedia Commons"
    SOURCE = "wikimedia"
    API = "https://commons.wikimedia.org/w/api.php"
    CATEGORIES = {
        "landscape": "Oil paintings of landscapes",
        "seascape": "Oil paintings of seascapes",
        "veduta": "Oil paintings of cityscapes",
    }

    def _search(self, style):
        category = self.CATEGORIES.get(style, self.CATEGORIES["landscape"])
        data = self._get_json(self.API, params={
            "action": "query", "format": "json", "generator": "search",
            "gsrsearch": f'deepcat:"{category}" filetype:bitmap', "gsrnamespace": 6,
            "gsrlimit": 50, "gsrsort": "random",
            "prop": "imageinfo", "iiprop": "size|url|extmetadata",
            "iiextmetadatafilter": "ObjectName|Artist|DateTimeOriginal",
        })
        for page in data.get("query", {}).get("pages", {}).values():
            info = (page.get("imageinfo") or [{}])[0]
            meta = info.get("extmetadata", {})
            text = lambda key: _strip_html(meta.get(key, {}).get("value", ""))
            if re.match(r"\d{4}-\d\d-\d\d \d\d:", text("DateTimeOriginal")):
                continue  # camera timestamp: a gallery snapshot (glare, frame), not a reproduction
            yield self._painting(
                id=page["title"],
                title=text("ObjectName") or Path(page["title"].split(":", 1)[-1]).stem,
                artist=text("Artist") or "Unknown artist",
                year=text("DateTimeOriginal"),
                source_url=info.get("descriptionurl", ""),
                width=info.get("width"),
                height=info.get("height"),
            )

    def _image_url(self, painting, size):
        data = self._get_json(self.API, params={
            "action": "query", "format": "json", "titles": painting["id"],
            "prop": "imageinfo", "iiprop": "url", "iiurlwidth": size[0],
        })
        page = next(iter(data["query"]["pages"].values()))
        return page["imageinfo"][0]["thumburl"]
