from pydantic import BaseModel


class SemanticElement(BaseModel):
    tag: str
    text: str | None = None
    aria_label: str | None = None
    role: str | None = None
    selector: str


class LayoutElement(BaseModel):
    selector: str

    x: float
    y: float

    width: float
    height: float

    visible: bool


class SiteSnapshot(BaseModel):
    snapshot_id: str

    url: str
    hostname: str
    title: str

    captured_at: str

    semantic_elements: list[SemanticElement]

    layout_elements: list[LayoutElement]

    screenshot_path: str

    dom_path: str
