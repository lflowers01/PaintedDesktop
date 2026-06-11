"""History management for PaintedDesktop app."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional


class HistoryManager:
    """Manages history.json for tracking set wallpapers."""
    
    def __init__(self, data_dir: str):
        """Initialize history manager with app data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "history.json"
        self.history = self._load_history()
    
    def _load_history(self) -> list:
        """Load history from JSON file or return empty list."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return []
        return []
    
    def save(self):
        """Save history to JSON file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def add_entry(self, title: str, artist: str, year: Optional[str], source_institution: str,
                  source_url: str, image_url: str, painting_id: str, image_path: str) -> Dict:
        """Add a new wallpaper entry to history."""
        entry = {
            "title": title,
            "artist": artist,
            "year": year,
            "source_institution": source_institution,
            "source_url": source_url,
            "image_url": image_url,
            "painting_id": painting_id,
            "image_path": image_path,
            "date_set": datetime.now().isoformat(),
        }
        self.history.insert(0, entry)  # Most recent first
        self.save()
        return entry
    
    def get_used_ids(self) -> set:
        """Get set of all painting IDs that have been used."""
        return {entry["painting_id"] for entry in self.history}
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Get history entries, most recent first."""
        if limit:
            return self.history[:limit]
        return self.history
    
    def get_last_entry(self) -> Optional[Dict]:
        """Get the most recent entry."""
        return self.history[0] if self.history else None
