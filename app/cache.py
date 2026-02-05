import time
import hashlib
from typing import Any, Dict, Optional, Tuple

class TTLCache:
    def __init__(self, ttl_seconds: int = 3600, max_items: int = 500):
        self.ttl = ttl_seconds
        self.max_items = max_items
        self._store: Dict[str, Tuple[float, Any]] = {}

    def _evict_if_needed(self):
        if len(self._store) <= self.max_items:
            return
        # Evict oldest
        oldest_key = min(self._store.items(), key=lambda kv: kv[1][0])[0]
        self._store.pop(oldest_key, None)

    @staticmethod
    def make_key(model: str, system_text: str, user_text: str) -> str:
        h = hashlib.sha256()
        h.update(model.encode("utf-8"))
        h.update(b"\n")
        h.update(system_text.encode("utf-8"))
        h.update(b"\n")
        h.update(user_text.encode("utf-8"))
        return h.hexdigest()

    def get(self, key: str) -> Optional[Any]:
        item = self._store.get(key)
        if not item:
            return None
        ts, value = item
        if time.time() - ts > self.ttl:
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = (time.time(), value)
        self._evict_if_needed()
