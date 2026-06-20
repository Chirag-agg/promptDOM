from enum import Enum
from pydantic import BaseModel


class WebsiteArchetype(str, Enum):
    CONTENT_FEED_PLATFORM = "CONTENT_FEED_PLATFORM"
    SOCIAL_NETWORK = "SOCIAL_NETWORK"
    PRODUCTIVITY_APP = "PRODUCTIVITY_APP"
    DASHBOARD = "DASHBOARD"
    DOCUMENT_EDITOR = "DOCUMENT_EDITOR"
    ECOMMERCE = "ECOMMERCE"
    SEARCH_ENGINE = "SEARCH_ENGINE"
    MEDIA_PLATFORM = "MEDIA_PLATFORM"
    FORUM = "FORUM"
    UNKNOWN = "UNKNOWN"


class WebsitePattern(str, Enum):
    LEFT_SIDEBAR_LAYOUT = "LEFT_SIDEBAR_LAYOUT"
    TOP_NAV_LAYOUT = "TOP_NAV_LAYOUT"
    CARD_FEED = "CARD_FEED"
    INFINITE_SCROLL = "INFINITE_SCROLL"
    COMMENT_THREAD = "COMMENT_THREAD"
    VIDEO_GRID = "VIDEO_GRID"
    SEARCH_CENTRIC = "SEARCH_CENTRIC"
    DASHBOARD_WIDGETS = "DASHBOARD_WIDGETS"
    PRODUCT_GRID = "PRODUCT_GRID"


class ArchetypeResult(BaseModel):
    snapshot_id: str

    archetype: WebsiteArchetype
    confidence: float

    evidence: list[str]
    competing_archetypes: list[str]
    archetype_scores: dict[str, int]

    patterns: list[WebsitePattern]
