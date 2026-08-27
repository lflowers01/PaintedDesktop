"""API fetchers for art sources."""

import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class ARTICFetcher:
    def __init__(self):
        self.session = requests.Session()
        # Set a real browser User-Agent to avoid 403 Forbidden errors
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'AIC-User-Agent': 'PaintedDesktop/1.0'
        })

    def search(self, subject: str, limit: int = 10) -> List[Dict]:
        try:
            params = {
                'q': f'oil paint {subject}',
                'query[type]': 'painting',
                'limit': limit,
                'fields': 'id,title,image_id,artist_title,date_display'
            }
            response = self.session.get('https://api.artic.edu/api/v1/artworks/search', params=params)
            response.raise_for_status()
            
            data = response.json()
            paintings = []
            if 'data' in data:
                for artwork in data['data']:
                    if artwork.get('image_id'):
                        paintings.append({
                            'id': artwork['id'],
                            'title': artwork.get('title', ''),
                            'artist': artwork.get('artist_title', ''),
                            'date': artwork.get('date_display', ''),
                            'image_id': artwork['image_id']
                        })
            return paintings
        except Exception as e:
            logger.error(f"ARTIC search error: {e}")
            return []

    def fetch_image(self, painting: Dict, min_resolution: Tuple[int, int], cache_dir: Path) -> Optional[str]:
        try:
            # Construct the IIIF image URL
            image_id = painting['image_id']
            if not image_id:
                return None
                
            # Use the IIIF API to get the image
            iiif_url = f"https://www.artic.edu/iiif/2/{image_id}/full/843,/0/default.jpg"
            
            response = self.session.get(iiif_url)
            response.raise_for_status()
            
            # Save the image to cache
            cache_path = cache_dir / f"{painting['id']}.jpg"
            with open(cache_path, 'wb') as f:
                f.write(response.content)
                
            return str(cache_path)
        except Exception as e:
            logger.error(f"ARTIC image fetch error: {e}")
            return None

class RijksmuseumFetcher:
    def __init__(self):
        self.session = requests.Session()
        # Set a real browser User-Agent to avoid 403 Forbidden errors
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def search(self, subject: str, limit: int = 10) -> List[Dict]:
        try:
            # Use the current Rijksmuseum API with correct parameters
            params = {
                'type': 'painting',
                'material': 'oil paint',
                'imageAvailable': 'true',
                'format': 'json'
            }
            
            # Add subject filter if provided (using description field)
            if subject:
                # Try to match landscape or seascape as described in the task
                if 'landscape' in subject.lower():
                    params['description'] = 'landscape'
                elif 'seascape' in subject.lower():
                    params['description'] = 'seascape'
            
            response = self.session.get('https://data.rijksmuseum.nl/search/collection', params=params)
            response.raise_for_status()
            
            data = response.json()
            paintings = []
            
            # Parse the orderedItems to get the PIDs
            if 'orderedItems' in data:
                for item in data['orderedItems']:
                    pid = item.get('id')
                    if pid:
                        paintings.append({
                            'id': pid,
                            'pid': pid  # Store the PID for later resolution
                        })
            
            return paintings[:limit]  # Return only requested limit
            
        except Exception as e:
            logger.error(f"Rijksmuseum search error: {e}")
            return []

    def fetch_image(self, painting: Dict, min_resolution: Tuple[int, int], cache_dir: Path) -> Optional[str]:
        try:
            # Get the object details by resolving the PID
            pid = painting.get('pid') or painting.get('id')
            if not pid:
                return None
                
            # Resolve the object to get image information
            object_url = f"{pid}?_profile=*"
            response = self.session.get(object_url)
            response.raise_for_status()
            
            object_data = response.json()
            
            # Extract image information from the representation
            representations = object_data.get('representation', [])
            if not representations:
                return None
                
            # Look for the IIIF image URL in the representations
            iiif_image_url = None
            direct_image_url = None
            
            for rep in representations:
                if isinstance(rep, dict):
                    # Check for IIIF service
                    if 'id' in rep and 'type' in rep and rep['type'] == 'ImageService2':
                        iiif_image_url = rep['id']
                    elif 'url' in rep and 'format' in rep:
                        # Direct image URL
                        direct_image_url = rep['url']
            
            # If we have IIIF info, we'll need to construct the image URL differently
            if iiif_image_url:
                # Use the IIIF image service to get full resolution
                image_url = f"{iiif_image_url}/full/full/0/default.jpg"
            elif direct_image_url:
                image_url = direct_image_url
            else:
                return None
            
            # Fetch the actual image
            response = self.session.get(image_url)
            response.raise_for_status()
            
            # Save the image to cache
            cache_path = cache_dir / f"{pid.split('/')[-1]}.jpg"
            with open(cache_path, 'wb') as f:
                f.write(response.content)
                
            return str(cache_path)
        except Exception as e:
            logger.error(f"Rijksmuseum image fetch error: {e}")
            return None

class WikimediaFetcher:
    def __init__(self):
        self.session = requests.Session()
        # Set a real browser User-Agent to avoid bot blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def search(self, subject: str, limit: int = 10) -> List[Dict]:
        try:
            # Use the MediaWiki API to search for images
            params = {
                'action': 'query',
                'list': 'search',
                'srsearch': f'filetype:image {subject}',
                'srnamespace': 6,  # File namespace
                'srlimit': limit,
                'format': 'json'
            }
            
            response = self.session.get('https://commons.wikimedia.org/w/api.php', params=params)
            response.raise_for_status()
            
            data = response.json()
            paintings = []
            
            if 'query' in data and 'search' in data['query']:
                for result in data['query']['search']:
                    file_title = result.get('title')
                    if file_title:
                        paintings.append({
                            'id': file_title,
                            'title': file_title
                        })
            
            return paintings
            
        except Exception as e:
            logger.error(f"Wikimedia search error: {e}")
            return []

    def fetch_image(self, painting: Dict, min_resolution: Tuple[int, int], cache_dir: Path) -> Optional[str]:
        try:
            # Get image info using the MediaWiki API
            file_title = painting.get('id')
            if not file_title:
                return None
                
            params = {
                'action': 'query',
                'titles': file_title,
                'prop': 'imageinfo',
                'iiprop': 'url|size',
                'format': 'json'
            }
            
            response = self.session.get('https://commons.wikimedia.org/w/api.php', params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract image information
            pages = data.get('query', {}).get('pages', {})
            if not pages:
                return None
                
            page_id = list(pages.keys())[0]
            imageinfo = pages[page_id].get('imageinfo', [])
            
            if not imageinfo:
                return None
                
            info = imageinfo[0]
            image_url = info.get('url')
            width = info.get('width', 0)
            height = info.get('height', 0)
            
            # Check resolution
            if width < min_resolution[0] or height < min_resolution[1]:
                return None
                
            if not image_url:
                return None
            
            # Download the image
            response = self.session.get(image_url)
            response.raise_for_status()
            
            # Save the image to cache
            cache_path = cache_dir / f"{file_title.replace('File:', '').replace('/', '_')}.jpg"
            with open(cache_path, 'wb') as f:
                f.write(response.content)
                
            return str(cache_path)
        except Exception as e:
            logger.error(f"Wikimedia image fetch error: {e}")
            return None
