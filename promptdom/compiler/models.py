from typing import Union, Annotated, List, Literal, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
import uuid

def get_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"

# Base Action Models

class ActionBase(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))

class HideElementAction(ActionBase):
    action_type: Literal["hide_element"] = "hide_element"
    selector: str

class ShowElementAction(ActionBase):
    action_type: Literal["show_element"] = "show_element"
    selector: str

class HighlightElementAction(ActionBase):
    action_type: Literal["highlight_element"] = "highlight_element"
    selector: str

class MonitorElementAction(ActionBase):
    action_type: Literal["monitor_element"] = "monitor_element"
    selector: str

class PeriodicTaskAction(ActionBase):
    action_type: Literal["periodic_task"] = "periodic_task"
    interval_ms: int
    operation: str

class TextMatchHighlightAction(ActionBase):
    action_type: Literal["text_match_highlight"] = "text_match_highlight"
    selector: str
    pattern: str

class NotifyAction(ActionBase):
    action_type: Literal["notify"] = "notify"
    title: str
    message: str

class ObserveElementAction(ActionBase):
    action_type: Literal["observe_element"] = "observe_element"
    selector: str
    event: Literal["ELEMENT_ADDED", "ELEMENT_REMOVED", "TEXT_CHANGED"]

ActionSpec = Annotated[Union[
    HideElementAction, 
    ShowElementAction, 
    HighlightElementAction, 
    MonitorElementAction, 
    PeriodicTaskAction, 
    TextMatchHighlightAction,
    NotifyAction,
    ObserveElementAction
], Field(discriminator="action_type")]

class FeatureSpec(BaseModel):
    name: str
    actions: List[ActionSpec] = Field(default_factory=list)

class CompiledFeature(BaseModel):
    javascript: str
    source_spec: FeatureSpec
    ast: 'FeatureAST'
    compiler_version: str = "1.0"
    compiled_at: str = Field(default_factory=get_utc_now)

from .ast import FeatureAST
CompiledFeature.model_rebuild()
