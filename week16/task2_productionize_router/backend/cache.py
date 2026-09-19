"""Process-local LRU+TTL cache. Fine for one worker; use Redis if you scale out."""
import time
from collections import OrderedDict
from typing import Any, Optional


class TTLCache:
    def __init__(self, max_size: int, ttl_seconds: int):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._data: OrderedDict[str, tuple[float, Any]] = OrderedDict()

    def get(self, key: str) -> Optional[Any]:
        item = self._data.get(key)
        if item is None:
            return None
        stamped_at, value = item
        if time.time() - stamped_at > self.ttl_seconds:
            del self._data[key]
            return None
        self._data.move_to_end(key)
        return value

    def set(self, key: str, value: Any) -> None:
        self._data[key] = (time.time(), value)
        self._data.move_to_end(key)
        while len(self._data) > self.max_size:
            self._data.popitem(last=False)
