from pydantic import BaseModel
from typing import Literal, Optional


class ActionRequest(BaseModel):
    prompt: str


class ActionResponse(BaseModel):
    success: bool
    action: dict
    message: Optional[str] = None


class FeatureAction(BaseModel):
    action: Literal["hide", "show", "highlight", "unhighlight"]
    target: Literal["youtube_shorts", "comments", "sidebar"]