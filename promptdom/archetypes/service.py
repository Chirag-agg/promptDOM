from promptdom.capture.models import SiteSnapshot
from promptdom.intelligence.models import WebsiteModel
from .models import ArchetypeResult
from .detector import ArchetypeDetector


class ArchetypeService:
    """Service to detect the underlying archetype of a website."""

    def __init__(self):
        self.detector = ArchetypeDetector()

    def detect(self, snapshot: SiteSnapshot, website_model: WebsiteModel) -> ArchetypeResult:
        """Detect the archetype based on raw capture data and structured intelligence."""
        return self.detector.detect(snapshot, website_model)
