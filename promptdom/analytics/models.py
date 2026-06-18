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
    error: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None

class PlanningLog(BaseModel):
    timestamp: str = Field(default_factory=get_utc_now)
    prompt: str
    planner_source: str
    success: bool
    execution_time_ms: float
    fallback_reason: Optional[str] = None

class PlannerComparisonLog(BaseModel):
    timestamp: str = Field(default_factory=get_utc_now)
    prompt: str
    rule_target: str
    llm_target: str
    agreed: bool

class FeatureCompilationLog(BaseModel):
    timestamp: str = Field(default_factory=get_utc_now)
    feature_type: str
    success: bool
    compile_ms: float

class RuntimeEventLog(BaseModel):
    timestamp: str = Field(default_factory=get_utc_now)
    feature_id: str
    runtime_instance_id: str
    event: str

class DesignPlanLog(BaseModel):
    timestamp: str = Field(default_factory=get_utc_now)
    prompt: str
    confidence: float
    plan_size: int

from ..visual.models import VisualContext
from ..design.models import DesignPlan

class TransformFeedbackLog(BaseModel):
    timestamp: str = Field(default_factory=get_utc_now)
    prompt: str
    design_plan: Optional[DesignPlan] = None
    css: str
    javascript: str
    worked: bool
    score: int
    notes: Optional[str] = None
    visual_context: Optional[VisualContext] = None

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

class PlannerDisagreementMetrics(BaseModel):
    disagreement_rate: float
    sample_count: int

class FeatureTimeline(BaseModel):
    created_at: str
    applications: List[ApplicationLog]
    repairs: List[RepairLog]

class RecentAnalytics(BaseModel):
    applications: List[ApplicationLog]
    repairs: List[RepairLog]
