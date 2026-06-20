from ..browser import BrowserManager
from ..inspection.service import InspectionService
from .models import VisualInspectionResponse
from .storage import ScreenshotStorage

class VisualInspectionService:
    def __init__(self, browser_manager: BrowserManager, inspection_service: InspectionService):
        self.browser_manager = browser_manager
        self.inspection_service = inspection_service
        self.storage = ScreenshotStorage()

    async def capture_context(self) -> VisualInspectionResponse:
        page_context = await self.inspection_service.inspect_compact()
        image_bytes = await self.browser_manager.take_screenshot(full_page=False)
        
        # We assume 1920x1080 if viewport isn't readily available, 
        # or we could get the viewport from the page.
        try:
            target_page = await self.browser_manager.get_active_page()
            viewport = target_page.viewport_size
            width = viewport["width"] if viewport else 1920
            height = viewport["height"] if viewport else 1080
        except:
            width, height = 1920, 1080
            
        visual_context = self.storage.save(
            image_bytes=image_bytes,
            page_url=page_context.url,
            width=width,
            height=height
        )
        
        return VisualInspectionResponse(
            page_context=page_context,
            visual_context=visual_context
        )
