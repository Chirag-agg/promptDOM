from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from ..inspection.models import CompactInspectionResponse

class ActionPlan(BaseModel):
    action: str
    target: str
    target_type: Literal["section", "button", "link", "input", "heading", "unknown"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    planner_source: str = "RULE"
    fallback_reason: Optional[str] = None

class PlannerContext(BaseModel):
    prompt: str
    page_context: CompactInspectionResponse

class PlannerResult(BaseModel):
    success: bool = True
    failure_reason: Optional[str] = None
    plans: List[ActionPlan] = Field(default_factory=list, max_length=5)

class HybridSelection(BaseModel):
    selected: str

class PlannerComparisonResponse(BaseModel):
    rule: PlannerResult
    llm: PlannerResult
    hybrid: HybridSelection
    agreement: bool
    winner: str
    ground_truth_available: bool
    rule_correct: Optional[bool] = None
    llm_correct: Optional[bool] = None
    hybrid_correct: Optional[bool] = None
    rule_latency_ms: float
    llm_latency_ms: float