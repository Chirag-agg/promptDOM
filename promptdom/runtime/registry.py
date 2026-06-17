from typing import Dict, List, Optional
from .models import RuntimeFeature, FeatureState
from datetime import datetime, timezone

def get_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"

class RuntimeRegistry:
    def __init__(self):
        self._features: Dict[str, RuntimeFeature] = {}

    def register(self, feature: RuntimeFeature) -> None:
        self._features[feature.runtime_instance_id] = feature

    def get(self, instance_id: str) -> Optional[RuntimeFeature]:
        return self._features.get(instance_id)
        
    def get_by_feature_id(self, feature_id: str) -> List[RuntimeFeature]:
        return [f for f in self._features.values() if f.feature_id == feature_id]

    def update_state(self, instance_id: str, state: FeatureState, error: Optional[str] = None, heartbeat: Optional[int] = None) -> None:
        if instance_id in self._features:
            f = self._features[instance_id]
            f.state = state
            f.last_seen_at = get_utc_now()
            if error is not None:
                f.error = error
            if heartbeat is not None:
                f.last_heartbeat = heartbeat

    def list_all(self) -> List[RuntimeFeature]:
        return list(self._features.values())
        
    def list_by_state(self, state: FeatureState) -> List[RuntimeFeature]:
        return [f for f in self._features.values() if f.state == state]
        
    def remove(self, instance_id: str) -> None:
        if instance_id in self._features:
            self._features[instance_id].state = FeatureState.REMOVED
