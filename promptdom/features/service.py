from typing import List, Optional
from .models import FeatureCreate, Feature
from .store import FeatureStore

class FeatureService:
    def __init__(self, store: FeatureStore):
        self.store = store

    def create_feature(self, data: FeatureCreate) -> Feature:
        feature = Feature(**data.model_dump())
        return self.store.create_feature(feature)

    def get_feature(self, feature_id: str) -> Optional[Feature]:
        return self.store.get_feature(feature_id)

    def list_features(self) -> List[Feature]:
        return self.store.list_features()

    def update_feature(self, feature_id: str, updates: dict) -> Optional[Feature]:
        for field in ['name', 'selector', 'hostname', 'action']:
            if field in updates:
                val = updates[field]
                if not val or not str(val).strip():
                    raise ValueError(f"{field} must not be empty")
                updates[field] = str(val).strip()
                
        return self.store.update_feature(feature_id, updates)

    def toggle_feature(self, feature_id: str) -> Optional[Feature]:
        return self.store.toggle_feature(feature_id)

    def delete_feature(self, feature_id: str) -> bool:
        return self.store.delete_feature(feature_id)
