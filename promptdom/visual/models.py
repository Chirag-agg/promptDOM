from pydantic import BaseModel
from ..inspection.models import CompactInspectionResponse

class VisualContext(BaseModel):
    screenshot_id: str
    screenshot_path: str
    page_url: str
    width: int
    height: int
    created_at: str

class VisualInspectionResponse(BaseModel):
    page_context: CompactInspectionResponse
    visual_context: VisualContext
