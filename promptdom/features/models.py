from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime, timezone
from uuid import uuid4

def get_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"

class FeatureCreate(BaseModel):
    name: str
    prompt: str
    source: str
    hostname: str
    page_type: str
    target: str
    target_type: str
    action: str
    selector: str

    @field_validator('name', 'selector', 'hostname', 'action')
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Must not be empty')
        return v.strip()

class Feature(FeatureCreate):
    id: str = Field(default_factory=lambda: str(uuid4()))
    enabled: bool = True
    created_at: str = Field(default_factory=get_utc_now)
    repair_count: int = 0
    last_repaired_at: Optional[str] = None
    last_status: str = "unknown"
    last_seen_at: Optional[str] = None
    feature_spec: Optional[dict] = None
    compiler_version: Optional[str] = None
    compiled_javascript: Optional[str] = None
