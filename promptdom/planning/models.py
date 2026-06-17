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
    plans: List[ActionPlan] = Field(max_length=5)
