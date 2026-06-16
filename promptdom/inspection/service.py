from typing import Dict, Any
from ..browser import BrowserManager
from .extractor import DOMExtractor
from .models import InspectionResponse, CompactInspectionResponse, ResolutionInspectionResponse

class InspectionService:
    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager
        self.extractor = DOMExtractor()

    async def inspect(self) -> InspectionResponse:
        page = await self.browser_manager.get_active_page()
        raw_data = await self.extractor.extract(page)
        return InspectionResponse(**raw_data)

    async def inspect_compact(self) -> CompactInspectionResponse:
        page = await self.browser_manager.get_active_page()
        raw_data = await self.extractor.extract(page)
        return CompactInspectionResponse(**raw_data)

    async def inspect_resolution(self) -> ResolutionInspectionResponse:
        page = await self.browser_manager.get_active_page()
        raw_data = await self.extractor.extract(page)
        return ResolutionInspectionResponse(**raw_data)
