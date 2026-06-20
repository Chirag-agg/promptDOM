import uuid
from datetime import datetime, timezone
from urllib.parse import urlparse

from ..browser import BrowserManager
from .models import SiteSnapshot
from .extractor import SiteExtractor
from .storage import CaptureStorage


class CaptureService:
    """Orchestrates the full site capture flow.

    Captures screenshot, semantic elements, layout data, and cleaned DOM
    for any website the browser is currently viewing.
    """

    def __init__(self, browser_manager: BrowserManager, storage: CaptureStorage):
        self.browser_manager = browser_manager
        self.storage = storage
        self.extractor = SiteExtractor(browser_manager)

    async def capture_current_page(self) -> SiteSnapshot:
        """
        Capture the current browser page.

        Flow:
            1. Take screenshot
            2. Extract semantic elements (buttons, links, inputs, headings, ARIA)
            3. Extract layout data (bounding rects)
            4. Extract and clean DOM
            5. Build SiteSnapshot
            6. Persist via CaptureStorage
            7. Return SiteSnapshot
        """
        # 1. Screenshot
        screenshot_bytes = await self.browser_manager.take_screenshot(full_page=False)

        # 2. Semantic extraction
        url, title, semantic_elements = await self.extractor.extract_semantic()

        # 3. Layout extraction
        layout_elements = await self.extractor.extract_layout()

        # 4. Cleaned DOM
        dom_html = await self.extractor.extract_cleaned_dom()

        # 5. Build snapshot
        snapshot_id = str(uuid.uuid4())
        captured_at = datetime.now(timezone.utc).isoformat()
        hostname = urlparse(url).hostname or "unknown"

        snapshot = SiteSnapshot(
            snapshot_id=snapshot_id,
            url=url,
            hostname=hostname,
            title=title,
            captured_at=captured_at,
            semantic_elements=semantic_elements,
            layout_elements=layout_elements,
            screenshot_path=f"data/captures/{snapshot_id}/screenshot.png",
            dom_path=f"data/captures/{snapshot_id}/dom.html",
        )

        # 6. Persist
        snapshot = self.storage.save_snapshot(snapshot, screenshot_bytes, dom_html)

        # 7. Return
        return snapshot
