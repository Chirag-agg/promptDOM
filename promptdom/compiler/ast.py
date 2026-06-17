from pydantic import BaseModel, Field
from typing import Dict, Any, List

class ActionAST(BaseModel):
    action_id: str
    action_type: str
    selector: str | None = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

class FeatureAST(BaseModel):
    name: str
    actions: List[ActionAST] = Field(default_factory=list)
