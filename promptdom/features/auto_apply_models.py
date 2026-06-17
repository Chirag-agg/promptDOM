from pydantic import BaseModel, Field
from typing import List
from datetime import datetime, timezone

def get_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"

class AppliedFeature(BaseModel):
    feature_id: str
    feature_name: str
    success: bool
    execution_time_ms: float
    message: str
    page_url: str
    applied_at: str = Field(default_factory=get_utc_now)

class AutoApplyResult(BaseModel):
    total_matches: int
    applied_count: int
    skipped_count: int
    failed_count: int
    results: List[AppliedFeature]
