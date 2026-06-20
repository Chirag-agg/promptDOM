from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..design.models import DesignPlan
from ..redesign.models import IterationRecord

class TransformationHistoryRecord(BaseModel):
    run_id: str
    prompt: str
    site: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str  # SUCCESS, PARTIAL, FAILED
    
    reference_id: Optional[str] = None
    design_plan: DesignPlan
    
    css: str
    javascript: str
    
    before_screenshot_path: str
    after_screenshot_path: str
    reference_screenshot_path: Optional[str] = None
    
    objective_metrics: Dict[str, Any]
    iterations: List[IterationRecord]
    
    diff_summary: Optional[str] = None
