import os
import json
from .models import KnowledgePack


class KnowledgeStorage:
    def __init__(self, base_dir: str = "data/knowledge"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_path(self, hostname: str) -> str:
        return os.path.join(self.base_dir, f"{hostname}.json")

    def save(self, pack: KnowledgePack):
        with open(self._get_path(pack.hostname), "w", encoding="utf-8") as f:
            f.write(pack.model_dump_json(indent=2))

    def load(self, hostname: str) -> KnowledgePack | None:
        path = self._get_path(hostname)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return KnowledgePack(**data)
        except Exception:
            return None

    def list_packs(self) -> list[KnowledgePack]:
        packs = []
        for filename in os.listdir(self.base_dir):
            if filename.endswith(".json"):
                hostname = filename[:-5]
                pack = self.load(hostname)
                if pack:
                    packs.append(pack)
        return sorted(packs, key=lambda p: p.hostname)
