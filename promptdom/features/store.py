import json
import os
from typing import List, Optional
from .models import Feature

class FeatureStore:
    def __init__(self, data_file: str = "data/features.json"):
        self.data_file = data_file
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        if not os.path.exists(self.data_file):
            self._write_file([])

    def _read_file(self) -> List[dict]:
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_file(self, data: List[dict]):
        tmp_file = f"{self.data_file}.tmp"
        with open(tmp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_file, self.data_file)

    def list_features(self) -> List[Feature]:
        data = self._read_file()
        return [Feature(**f) for f in data]

    def get_feature(self, feature_id: str) -> Optional[Feature]:
        for f in self._read_file():
            if f.get('id') == feature_id:
                return Feature(**f)
        return None

    def create_feature(self, feature: Feature) -> Feature:
        data = self._read_file()
        data.append(feature.model_dump())
        self._write_file(data)
        return feature

    def update_feature(self, feature_id: str, updates: dict) -> Optional[Feature]:
        data = self._read_file()
        for i, f in enumerate(data):
            if f.get('id') == feature_id:
                # Update only the allowed keys, or just let pydantic handle validation
                for k, v in updates.items():
                    if k in f:
                        f[k] = v
                feature = Feature(**f)
                data[i] = feature.model_dump()
                self._write_file(data)
                return feature
        return None

    def toggle_feature(self, feature_id: str) -> Optional[Feature]:
        data = self._read_file()
        for i, f in enumerate(data):
            if f.get('id') == feature_id:
                f['enabled'] = not f.get('enabled', True)
                feature = Feature(**f)
                data[i] = feature.model_dump()
                self._write_file(data)
                return feature
        return None

    def delete_feature(self, feature_id: str) -> bool:
        data = self._read_file()
        filtered_data = [f for f in data if f.get('id') != feature_id]
        if len(data) == len(filtered_data):
            return False
        self._write_file(filtered_data)
        return True
