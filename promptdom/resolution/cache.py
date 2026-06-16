from typing import Optional
import json
import os

class ResolutionCache:
    def __init__(self, cache_file: str = "resolution_cache.json"):
        self.cache_file = cache_file
        self._cache = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f)
        except Exception:
            pass

    def _make_key(self, fingerprint: str, target: str, target_type: str) -> str:
        return f"{fingerprint}_{target}_{target_type}"

    def get(self, fingerprint: str, target: str, target_type: str) -> Optional[str]:
        key = self._make_key(fingerprint, target, target_type)
        return self._cache.get(key)

    def set(self, fingerprint: str, target: str, target_type: str, selector: str):
        key = self._make_key(fingerprint, target, target_type)
        self._cache[key] = selector
        self._save()
