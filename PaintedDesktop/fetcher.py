"""API fetchers for art sources."""

import requests
import logging
from typing import Optional, Tuple, Dict, List
from PIL import Image
from io import BytesIO
from pathlib import Path
import os


logger = logging.getLogger(__name__)

# API timeouts and retries
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3


class ARTICFetcher:
    """Art Institute of Chicago API fetcher."""
    
    BASE_URL = "https://api.artic.edu/api/v1/artworks/search"
    IMAGE_BASE_URL = "https://www.artic.edu/iiif/2"
    
    def search(self, subject: str, limit: int = 100) -> List[Dict]:
        """
        Search ARTIC for paintings.
        
        Args:
            subject: 'landscape' or 'seascape'
            limit: Number of results to fetch
            
        Returns:
            List of painting dicts
        """
        params = {
            'q': f'oil {subject}',
            'limit': limit,
            'fields': [
                'id',
                'title',
                'artist_display',
                'date_display',
                'medium_display',
                'subject_titles',
                'image_id',
                'dimensions',
            ]
        }
        
        try:
            response = requests.post(
                self.BASE_URL,
                json=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except Exception as e:
            logger.error(f"ARTIC search error: {e}")
            return []
    
    def get_image_url(self, image_id: str, width: int = 1920) -> str:
        """
        Get IIIF image URL.
        
        Args:
            image_id: Image ID from ARTIC
            width: Requested width
            
        Returns:
            Image URL
        """
        if not image_id:
            return None
        return f"{self.IMAGE_BASE_URL}/{image_id}/full/{width},/0/default.jpg"
    
    def fetch_image(self, painting: Dict, min_resolution: Tuple[int, int],
                    cache_dir: Path) -> Optional[str]:
        """
        Fetch and validate image.
        
        Args:
            painting: Painting dict from search results
            min_resolution: (width, height) minimum
            cache_dir: Directory to cache image
            
        Returns:
            Path to cached image or None
        """
        image_id = painting.get('image_id')
        if not image_id:
            return None
        
        painting_id = painting.get('id')
        if not painting_id:
            return None
        
        # Try different resolutions
        for width in [min_resolution[0] * 2, min_resolution[0], 1920]:
            try:
                url = self.get_image_url(image_id, width)
                response = requests.get(url, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                
                # Validate image
                img = Image.open(BytesIO(response.content))
                img_width, img_height = img.size
                
                if img_width >= min_resolution[0] and img_height >= min_resolution[1]:
                    # Cache image
                    filename = f"{painting_id}.jpg"
                    filepath = cache_dir / filename
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    logger.info(f"Cached image: {filepath}")
                    return str(filepath)
                else:
                    logger.debug(f"Image too small: {img_width}x{img_height}")
            except Exception as e:
                logger.debug(f"Error fetching ARTIC image: {e}")
                continue
        
        return None


class RijksmuseumFetcher:
    """Rijksmuseum API fetcher."""
    
    BASE_URL = "https://data.rijksmuseum.nl/search/collection"
    
    
    def search(self, subject: str, limit: int = 100) -> List[Dict]:
        """
        Search Rijksmuseum for paintings.
        
        Args:
            subject: 'landscape' or 'seascape'
            limit: Number of results
            
        Returns:
            List of painting dicts
        """
    
        
        params = {
            'format': 'json',
            'imgonly': True,
            'ps': limit,
            'p': 1,
        }
        
        # Add filters based on subject
        if subject == 'landscape':
            params['type'] = 'painting'
            params['material'] = 'oil paint'
            params['f.type.en.norm'] = 'landscape'
        elif subject == 'seascape':
            params['type'] = 'painting'
            params['f.type.en.norm'] = 'seascape'
        
        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data.get('artObjects', [])
        except Exception as e:
            logger.error(f"Rijksmuseum search error: {e}")
            return []
    
    def fetch_image(self, painting: Dict, min_resolution: Tuple[int, int],
                    cache_dir: Path) -> Optional[str]:
        """
        Fetch and validate image.
        
        Args:
            painting: Painting dict from search results
            min_resolution: (width, height) minimum
            cache_dir: Directory to cache image
            
        Returns:
            Path to cached image or None
        """
        web_image = painting.get('webImage', {})
        if not web_image:
            return None
        
        url = web_image.get('url')
        if not url:
            return None
        
        # Check resolution in metadata first
        img_width = web_image.get('width', 0)
        img_height = web_image.get('height', 0)
        
        if img_width < min_resolution[0] or img_height < min_resolution[1]:
            logger.debug(f"Image too small: {img_width}x{img_height}")
            return None
        
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Verify with PIL
            img = Image.open(BytesIO(response.content))
            img_width, img_height = img.size
            
            if img_width >= min_resolution[0] and img_height >= min_resolution[1]:
                painting_id = painting.get('id', painting.get('objectNumber', 'unknown'))
                filename = f"{painting_id}.jpg"
                filepath = cache_dir / filename
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                logger.info(f"Cached Rijksmuseum image: {filepath}")
                return str(filepath)
        except Exception as e:
            logger.error(f"Error fetching Rijksmuseum image: {e}")
        
        return None


class WikimediaFetcher:
    """Wikimedia Commons fallback fetcher."""
    
    BASE_URL = "https://commons.wikimedia.org/w/api.php"
    
    def search(self, subject: str, limit: int = 100) -> List[Dict]:
        """
        Search Wikimedia Commons for paintings.
        
        Args:
            subject: 'landscape' or 'seascape'
            limit: Number of results
            
        Returns:
            List of painting dicts
        """
        search_term = f"{subject} painting oil"
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': search_term,
            'srnamespace': 6,  # File namespace
            'srlimit': limit,
        }
        
        try:
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()
            return data.get('query', {}).get('search', [])
        except Exception as e:
            logger.error(f"Wikimedia search error: {e}")
            return []
    
    def fetch_image(self, painting: Dict, min_resolution: Tuple[int, int],
                    cache_dir: Path) -> Optional[str]:
        """
        Fetch and validate image (simplified for Wikimedia).
        
        Returns:
            Path to cached image or None
        """
        # Wikimedia is kept as fallback; basic implementation
        logger.info("Wikimedia fallback - skipping for now")
        return None
