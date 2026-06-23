import os
import json
from typing import List, Dict, Optional
from .models import SavedTransformation

class TransformationManager:
    def __init__(self, data_dir: str = "data/transformations"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
    def _get_filepath(self, hostname: str) -> str:
        return os.path.join(self.data_dir, f"{hostname}.json")
        
    def get_transformations(self, hostname: str) -> List[SavedTransformation]:
        filepath = self._get_filepath(hostname)
        if not os.path.exists(filepath):
            return []
            
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [SavedTransformation(**item) for item in data]
        except Exception as e:
            print(f"Error loading transformations for {hostname}: {e}")
            return []
            
    def save_transformation(self, transformation: SavedTransformation):
        filepath = self._get_filepath(transformation.hostname)
        transformations = self.get_transformations(transformation.hostname)
        
        # Check if exists, update if it does
        for i, t in enumerate(transformations):
            if t.id == transformation.id:
                transformations[i] = transformation
                break
        else:
            transformations.append(transformation)
            
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([t.model_dump() for t in transformations], f, indent=2)
            
    def delete_transformation(self, hostname: str, transformation_id: str):
        transformations = self.get_transformations(hostname)
        transformations = [t for t in transformations if t.id != transformation_id]
        
        filepath = self._get_filepath(hostname)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump([t.model_dump() for t in transformations], f, indent=2)
