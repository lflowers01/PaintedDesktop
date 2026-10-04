from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

from PIL import Image

from fetcher import ARTICFetcher, RijksmuseumFetcher, WikimediaFetcher, _strip_html, target_size

SCREEN = (2560, 1600)


def jpeg(width, height):
    buf = BytesIO()
    Image.new("RGB", (width, height), "blue").save(buf, "JPEG")
    return buf.getvalue()


def response(json=None, content=b""):
    r = MagicMock()
    r.json.return_value = json
    r.content = content
    return r


def test_target_size_fill_covers_screen():
    assert target_size(6000, 4000, SCREEN, "fill") == (2560, 1707)


def test_target_size_fit_fits_inside_screen():
    assert target_size(6000, 4000, SCREEN, "fit") == (2400, 1600)


def test_target_size_rejects_too_small_and_portraits():
    assert target_size(1920, 1080, SCREEN, "fill") is None
    assert target_size(3000, 6000, SCREEN, "fit") is None  # tall portrait
    assert target_size(None, None, SCREEN) is None


def test_strip_html_drops_hidden_wikidata_markup():
    raw = 'The Falls<div style="display: none;">label QS:Len,"The Falls"</div> &amp; more'
    assert _strip_html(raw) == "The Falls & more"


def test_artic_search_parses_and_skips_small_images():
    fetcher = ARTICFetcher(SCREEN, "fill")
    fetcher.session.post = MagicMock(return_value=response({
        "pagination": {"total_pages": 1},
        "data": [
            {"id": 1, "title": "Big", "image_id": "a", "artist_display": "Claude Monet\nFrench, 1840-1926",
             "date_display": "1890", "thumbnail": {"width": 6000, "height": 4000}},
            {"id": 2, "title": "Small", "image_id": "b", "artist_display": "X",
             "thumbnail": {"width": 800, "height": 600}},
        ],
    }))
    paintings = list(fetcher.candidates("landscape"))
    assert [p["id"] for p in paintings] == ["1"]
    assert paintings[0]["artist"] == "Claude Monet (French, 1840-1926)"
    query = fetcher.session.post.call_args.kwargs["json"]["query"]["bool"]
    assert {"match_phrase": {"subject_titles": "landscapes"}} in query["should"]
    assert {"match_phrase": {"subject_titles": "religion"}} in query["must_not"]


def test_search_errors_end_iteration_instead_of_raising():
    fetcher = ARTICFetcher(SCREEN)
    fetcher.session.post = MagicMock(side_effect=OSError("DNS failure"))
    assert list(fetcher.candidates("landscape")) == []


def test_fetch_image_requests_screen_size_and_caches(tmp_path):
    fetcher = ARTICFetcher(SCREEN, "fill")
    fetcher.session.get = MagicMock(return_value=response(content=jpeg(2560, 1707)))
    painting = fetcher._painting(id="27992", image_id="abc", width=6000, height=4000)
    path = fetcher.fetch_image(painting, tmp_path)
    assert path == str(tmp_path / "artic_27992.jpg") and Path(path).exists()
    assert fetcher.session.get.call_args.args[0].endswith("/abc/full/2560,/0/default.jpg")


def test_fetch_image_rejects_undersized_download(tmp_path):
    fetcher = ARTICFetcher(SCREEN, "fill")
    fetcher.session.get = MagicMock(return_value=response(content=jpeg(1024, 683)))
    painting = fetcher._painting(id="1", image_id="abc", width=6000, height=4000)
    assert fetcher.fetch_image(painting, tmp_path) is None
    assert list(tmp_path.iterdir()) == []


def test_rijksmuseum_resolves_linked_art_chain(tmp_path):
    english = [{"id": RijksmuseumFetcher.ENGLISH}]
    docs = {
        "https://id.rijksmuseum.nl/1": {
            "identified_by": [{"type": "Name", "content": "Landschap"},
                              {"type": "Name", "content": "Landscape", "language": english}],
            "produced_by": {"referred_to_by": [{"content": "Rembrandt van Rijn"}],
                            "timespan": {"identified_by": [{"content": "c. 1638", "language": english}]}},
            "subject_of": [{"digitally_carried_by": [{"access_point": [
                {"id": "https://www.rijksmuseum.nl/nl/collectie/object/SK-A-1"}]}]}],
            "shows": [{"id": "https://id.rijksmuseum.nl/2"}],
        },
        "https://id.rijksmuseum.nl/2": {"digitally_shown_by": [{"id": "https://id.rijksmuseum.nl/3"}]},
        "https://id.rijksmuseum.nl/3": {"access_point": [{"id": "https://iiif.micr.io/xyz/full/max/0/default.jpg"}]},
        "https://iiif.micr.io/xyz/info.json": {"width": 6108, "height": 4301},
    }
    fetcher = RijksmuseumFetcher(SCREEN, "fit")
    fetcher._get_json = lambda url, **kw: docs[url]
    fetcher.session.get = MagicMock(return_value=response(content=jpeg(2273, 1600)))
    painting = fetcher._painting(id="1", object_url="https://id.rijksmuseum.nl/1")

    assert fetcher.fetch_image(painting, tmp_path)
    assert painting["title"] == "Landscape" and painting["artist"] == "Rembrandt van Rijn"
    assert painting["year"] == "c. 1638"
    assert painting["source_url"] == "https://www.rijksmuseum.nl/en/collection/object/SK-A-1"
    assert painting["image_url"] == "https://iiif.micr.io/xyz/full/2273,/0/default.jpg"


def test_wikimedia_skips_gallery_photos():
    def page(title, date):
        return {"title": f"File:{title}.jpg", "imageinfo": [{"width": 6000, "height": 4000, "extmetadata": {
            "Artist": {"value": "<a>Albert Bierstadt</a>"}, "DateTimeOriginal": {"value": date}}}]}
    fetcher = WikimediaFetcher(SCREEN)
    fetcher._get_json = lambda url, **kw: {"query": {"pages": {
        "1": page("Reproduction", "1866"), "2": page("Snapshot", "2017-05-28 14:06:54")}}}
    paintings = list(fetcher.candidates("landscape"))
    assert [p["title"] for p in paintings] == ["Reproduction"]
    assert paintings[0]["artist"] == "Albert Bierstadt"
