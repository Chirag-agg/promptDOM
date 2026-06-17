from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, timezone
import uuid

def get_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"

class FeatureState(str, Enum):
    INSTALLED = "INSTALLED"
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"
    FAILED = "FAILED"
    REMOVED = "REMOVED"

class RuntimeFeature(BaseModel):
    feature_id: str
    runtime_instance_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    state: FeatureState = FeatureState.INSTALLED
    installed_at: str = Field(default_factory=get_utc_now)
    last_seen_at: Optional[str] = None
    last_heartbeat: Optional[int] = None
    error: Optional[str] = None
