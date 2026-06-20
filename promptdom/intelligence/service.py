from promptdom.capture.models import SiteSnapshot
from .models import WebsiteModel
from .analyzer import WebsiteAnalyzer
from .storage import IntelligenceStorage


class IntelligenceService:
    """Service for extracting structured intelligence from raw capture data."""

    def __init__(self):
        self.analyzer = WebsiteAnalyzer()
        self.storage = IntelligenceStorage()

    def analyze(self, snapshot: SiteSnapshot, force: bool = False) -> WebsiteModel:
        """Analyze a capture snapshot and return a structured website model. Caches the result."""
        if not force and self.storage.exists(snapshot.snapshot_id):
            cached = self.storage.load(snapshot.snapshot_id)
            if cached:
                return cached

        model = self.analyzer.analyze(snapshot)
        self.storage.save(snapshot.snapshot_id, model)
        return model
