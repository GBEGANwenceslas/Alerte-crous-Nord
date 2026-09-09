"""Persistance (fichier JSON) des logements déjà vus, pour ne notifier que les nouveautés."""
import json
from pathlib import Path
from typing import Set


class SeenStore:
    def __init__(self, path: str = "logements_vus.json"):
        self.path = Path(path)
        self._seen: Set[str] = set()
        if self.path.exists():
            try:
                self._seen = set(json.loads(self.path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                self._seen = set()

    def is_empty(self) -> bool:
        return len(self._seen) == 0

    def is_new(self, key: str) -> bool:
        return key not in self._seen

    def mark_seen(self, key: str) -> None:
        self._seen.add(key)

    def save(self) -> None:
        self.path.write_text(
            json.dumps(sorted(self._seen), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
