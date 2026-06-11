"""Filtering logic for art paintings."""

import logging
from typing import Dict, List, Optional


logger = logging.getLogger(__name__)


class PaintingFilter:
    """Filters paintings based on medium and genre."""
    
    VALID_MEDIUMS = {
        'oil on canvas',
        'oil on panel',
        'oil',
        'oil on wood',
        'oil on wood panel',
    }
    
    LANDSCAPE_KEYWORDS = {
        'landscape',
        'seascape',
        'veduta',
        'townscape',
        'architectural landscape',
        'view',
        'marine',
        'water',
    }
    
    def __init__(self, allowed_styles: Optional[List[str]] = None):
        """
        Initialize filter.
        
        Args:
            allowed_styles: List of allowed styles ('landscape', 'seascape', 'veduta')
        """
        self.allowed_styles = set(allowed_styles) if allowed_styles else {'landscape', 'seascape'}
    
    def _normalize_string(self, s: str) -> str:
        """Normalize string for comparison."""
        return s.lower().strip()
    
    def _check_medium(self, painting: Dict) -> bool:
        """Check if painting has valid oil medium."""
        medium = painting.get('medium_display', '')
        if medium:
            medium_norm = self._normalize_string(medium)
            for valid in self.VALID_MEDIUMS:
                if valid in medium_norm:
                    return True
        
        # Also check 'material' field from Rijksmuseum
        material = painting.get('material', [])
        if isinstance(material, list):
            for m in material:
                if 'oil' in self._normalize_string(str(m)):
                    return True
        
        return False
    
    def _check_genre(self, painting: Dict) -> bool:
        """Check if painting matches allowed landscape/seascape/veduta genre."""
        # Check multiple possible fields
        fields_to_check = [
            'subject_titles',
            'category_titles',
            'classification_titles',
            'subject_id',
            'subject',
            'type',
        ]
        
        for field in fields_to_check:
            values = painting.get(field, [])
            if isinstance(values, str):
                values = [values]
            elif not isinstance(values, list):
                values = []
            
            for value in values:
                val_norm = self._normalize_string(str(value))
                
                # Check if any allowed style matches
                if 'landscape' in self.allowed_styles:
                    if 'landscape' in val_norm or 'landscape painting' in val_norm:
                        return True
                
                if 'seascape' in self.allowed_styles:
                    if 'seascape' in val_norm or 'marine' in val_norm or 'water' in val_norm:
                        return True
                
                if 'veduta' in self.allowed_styles:
                    if 'veduta' in val_norm or 'townscape' in val_norm or 'architectural landscape' in val_norm:
                        return True
        
        return False
    
    def passes_filter(self, painting: Dict) -> bool:
        """
        Check if painting passes all filters.
        
        Args:
            painting: Painting dict with metadata
            
        Returns:
            True if painting passes filter
        """
        if not self._check_medium(painting):
            return False
        
        if not self._check_genre(painting):
            return False
        
        return True
