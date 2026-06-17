from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime, timezone

def get_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"

class ApplicationLog(BaseModel):
    timestamp: str = Field(default_factory=get_utc_now)
    feature_id: str
    success: bool
    execution_time_ms: float
    page_url: str

class RepairLog(BaseModel):
    timestamp: str = Field(default_factory=get_utc_now)
    feature_id: str
    old_selector: str
    new_selector: str
    confidence: float
    repair_method: str

class LLMRequestLog(BaseModel):
    timestamp: str = Field(default_factory=get_utc_now)
    provider: str
    model: str
    latency_ms: float
    success: bool
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None

class PlanningLog(BaseModel):
    timestamp: str = Field(default_factory=get_utc_now)
    prompt: str
    planner_source: str
    success: bool
    execution_time_ms: float
    fallback_reason: Optional[str] = None

class FeatureAnalytics(BaseModel):
    name: str
    apply_count: int
    success_rate: float
    repair_count: int
    average_execution_ms: float
    feature_decay_score: float
    last_seen_at: Optional[str]

class SiteAnalytics(BaseModel):
    hostname: str
    feature_count: int
    stale_features: int
    repair_count: int

class SystemHealth(BaseModel):
    total_features: int
    ready_features: int
    stale_features: int
    disabled_features: int
    repair_success_rate: float

class PlannerAnalytics(BaseModel):
    rule_usage: int
    llm_usage: int
    hybrid_rule_usage: int
    hybrid_llm_usage: int
    average_latency_ms: float

class FeatureTimeline(BaseModel):
    created_at: str
    applications: List[ApplicationLog]
    repairs: List[RepairLog]

class RecentAnalytics(BaseModel):
    applications: List[ApplicationLog]
    repairs: List[RepairLog]
