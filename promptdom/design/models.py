from pydantic import BaseModel, Field
from typing import List, Optional

class DesignChange(BaseModel):
    type: str = Field(description="One of: REMOVE, MOVE, RESTYLE, ADD")
    target: str = Field(description="Target element or concept")
    destination: Optional[str] = None
    style_goal: Optional[str] = None
    description: Optional[str] = None

class DesignPlan(BaseModel):
    goal: str
    reasoning: str
    changes: List[DesignChange]
    layout_strategy: str
    visual_strategy: str
    content_strategy: str
    confidence: float
