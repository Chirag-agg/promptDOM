from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from ..design.models import DesignPlan
from ..visual.models import VisualContext
from ..inspection.models import CompactInspectionResponse

class GoalType(str, Enum):
    DECLUTTER = "DECLUTTER"
    REMOVE_ELEMENT = "REMOVE_ELEMENT"
    RESTYLE = "RESTYLE"
    LAYOUT_CHANGE = "LAYOUT_CHANGE"
    REORGANIZE = "REORGANIZE"

class GoalAnalysis(BaseModel):
    primary_goal: GoalType = Field(description="The primary goal type for the prompt.")
    secondary_goals: List[GoalType] = Field(description="Any secondary goals that apply.", default_factory=list)
    reasoning: str = Field(description="Explanation of why these goal types were chosen.")

class EvaluationResult(BaseModel):
    worked: bool = Field(description="Whether the redesign successfully achieved the goals.")
    confidence: float = Field(description="Confidence score (0.0 to 1.0) in this evaluation.")
    feedback: str = Field(description="Detailed explanation of what worked and what didn't.")
    unresolved_targets: List[str] = Field(description="List of logical targets (e.g., 'Shorts shelf') that were not properly addressed.", default_factory=list)

class GroundedCandidate(BaseModel):
    selector: str = Field(description="The CSS selector for the candidate element.")
    confidence: float = Field(description="Confidence score (0.0 to 1.0) that this is the correct target.")
    reason: str = Field(description="Reasoning for selecting this candidate.")

class TransformationPatch(BaseModel):
    css_patch: str = Field(description="CSS to append or override previous attempts.")
    js_patch: str = Field(description="JavaScript to append or override previous attempts.")
    explanation: str = Field(description="Explanation of what this patch does.")

class IterationRecord(BaseModel):
    iteration: int = Field(description="The iteration number (1-indexed).")
    feedback: str = Field(description="The feedback received from the evaluator for this iteration.")
    selectors_found: List[str] = Field(description="The grounded selectors found by the repair service.")
    patch_generated: str = Field(description="The CSS patch generated to fix the issue.")
    success: bool = Field(description="Whether this iteration succeeded.")

class IterationContext(BaseModel):
    prompt: str = Field(description="The original user prompt.")
    goal: GoalAnalysis = Field(description="The defined goals for the transformation.")
    design_plan: DesignPlan = Field(description="The high-level design plan.")
    before_screenshot: str = Field(description="Base64 encoded original screenshot.")
    after_screenshot: str = Field(description="Base64 encoded screenshot after applying the current transformation.")
    dom_snapshot: CompactInspectionResponse = Field(description="The current DOM snapshot.")
    evaluator_feedback: str = Field(description="The feedback from the evaluator on the failure.")
    grounded_candidates: Dict[str, List[GroundedCandidate]] = Field(description="Ranked candidates for unresolved targets.", default_factory=dict)
