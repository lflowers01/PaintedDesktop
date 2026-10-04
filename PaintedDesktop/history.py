"""History of wallpapers that have been set (history.json, most recent first)."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


def write_json_atomic(path: Path, data) -> None:
    """Write JSON via a temp file so a crash mid-write can't corrupt the original."""
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


class HistoryManager:
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "history.json"
        self.history = self._load_history()

    def _load_history(self) -> list:
        try:
            data = json.loads(self.history_file.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (OSError, ValueError):
            return []

    def save(self):
        write_json_atomic(self.history_file, self.history)

    def add_entry(self, title: str, artist: str, year: Optional[str], source_institution: str,
                  source_url: str, image_url: str, painting_id: str, image_path: str) -> Dict:
        entry = {
            "title": title,
            "artist": artist,
            "year": year,
            "source_institution": source_institution,
            "source_url": source_url,
            "image_url": image_url,
            "painting_id": str(painting_id),
            "image_path": image_path,
            "date_set": datetime.now().isoformat(timespec="seconds"),
        }
        self.history.insert(0, entry)
        self.save()
        return entry

    def get_used_ids(self) -> set:
        """IDs of every painting already shown (as strings; older entries stored ints)."""
        return {str(entry.get("painting_id")) for entry in self.history}

    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        return self.history[:limit] if limit else self.history

    def get_last_entry(self) -> Optional[Dict]:
        return self.history[0] if self.history else None

    def last_set_time(self) -> Optional[datetime]:
        entry = self.get_last_entry()
        try:
            return datetime.fromisoformat(entry["date_set"]) if entry else None
        except (KeyError, TypeError, ValueError):
            return None
