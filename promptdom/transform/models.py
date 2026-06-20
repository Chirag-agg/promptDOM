from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class TransformationRequest(BaseModel):
    prompt: str
    reference_id: Optional[str] = None

class PlanRequest(BaseModel):
    prompt: str
    reference_id: Optional[str] = None

from ..design.models import DesignPlan

class ApplyRedesignRequest(BaseModel):
    prompt: str
    reference_id: Optional[str] = None
    design_plan: DesignPlan

class GeneratedTransformation(BaseModel):
    css: str
    javascript: str
    reasoning: str
    confidence: float
    affected_elements: List[str]
    transformation_type: str

from ..design.models import DesignPlan

class TransformationPreviewResponse(BaseModel):
    transformation_id: str
    prompt: str = ""
    design_plan: Optional[DesignPlan] = None
    transformation: GeneratedTransformation
    ui_diff_summary: str

class TransformExecutionRequest(BaseModel):
    transformation_id: str

class TransformExecutionResult(BaseModel):
    transformation_id: str
    success: bool
    applied_css: bool
    applied_javascript: bool
    message: str
    
    before_screenshot_path: str = ""
    after_screenshot_path: str = ""
    reference_screenshot_path: Optional[str] = None
    
    objective_metrics: Dict[str, Any] = Field(default_factory=dict)
    diff_summary: str = ""

class TransformTestResponse(BaseModel):
    preview: TransformationPreviewResponse
    execution: TransformExecutionResult

class TransformFeedbackRequest(BaseModel):
    transformation_id: str
    worked: bool
    score: int
    notes: Optional[str] = None
