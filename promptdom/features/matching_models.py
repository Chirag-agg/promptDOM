from pydantic import BaseModel
from typing import List

class FeatureMatch(BaseModel):
    feature_id: str
    feature_name: str
    confidence: float
    feature_health: float
    status: str
    reason: str

class MatchResult(BaseModel):
    page_hostname: str
    page_type: str
    matches: List[FeatureMatch]

class DiagnosticsResult(BaseModel):
    total_features: int
    ready: int
    partial: int
    stale: int
    disabled: int
