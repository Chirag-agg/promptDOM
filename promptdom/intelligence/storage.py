import os
import json
from datetime import datetime, timezone
from pydantic import BaseModel
from .models import WebsiteModel


class IntelligenceRecord(BaseModel):
    snapshot_id: str
    website_model: WebsiteModel
    generated_at: str


class IntelligenceStorage:
    def __init__(self, base_dir: str = "data/intelligence"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_path(self, snapshot_id: str) -> str:
        return os.path.join(self.base_dir, f"{snapshot_id}.json")

    def exists(self, snapshot_id: str) -> bool:
        return os.path.isfile(self._get_path(snapshot_id))

    def load(self, snapshot_id: str) -> WebsiteModel | None:
        path = self._get_path(snapshot_id)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                record = IntelligenceRecord(**data)
                return record.website_model
        except Exception:
            return None

    def save(self, snapshot_id: str, website_model: WebsiteModel):
        record = IntelligenceRecord(
            snapshot_id=snapshot_id,
            website_model=website_model,
            generated_at=datetime.now(timezone.utc).isoformat()
        )
        with open(self._get_path(snapshot_id), "w", encoding="utf-8") as f:
            f.write(record.model_dump_json(indent=2))
