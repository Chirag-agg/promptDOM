from pydantic import BaseModel
from typing import List, Optional

class TransformationRequest(BaseModel):
    prompt: str

class GeneratedTransformation(BaseModel):
    css: str
    javascript: str
    reasoning: str
    confidence: float
    affected_elements: List[str]
    transformation_type: str

class TransformationPreviewResponse(BaseModel):
    transformation_id: str
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

class TransformTestResponse(BaseModel):
    preview: TransformationPreviewResponse
    execution: TransformExecutionResult
