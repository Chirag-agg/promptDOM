from enum import Enum
from pydantic import BaseModel


class RegionType(str, Enum):
    HEADER = "HEADER"
    NAVIGATION = "NAVIGATION"
    SIDEBAR = "SIDEBAR"
    MAIN_CONTENT = "MAIN_CONTENT"
    FEED = "FEED"
    FOOTER = "FOOTER"
    FORM = "FORM"
    UNKNOWN = "UNKNOWN"


class PageRegion(BaseModel):
    region_id: str

    region_type: RegionType

    selector: str

    x: float
    y: float

    width: float
    height: float

    confidence: float

    evidence: list[str]


class WebsiteModel(BaseModel):
    snapshot_id: str

    regions: list[PageRegion]

    detected_patterns: list[str]
