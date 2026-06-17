import asyncio
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from .inspection.exceptions import BrowserUnavailableError, NoActivePageError, PageClosedError


class BrowserManager:
    def __init__(self, debugging_url: str = "http://localhost:9222"):
        self.debugging_url = debugging_url
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._initialized = False

    async def initialize(self):
        """Initialize connection to Chrome DevTools Protocol"""
        if self._initialized:
            return

        self.playwright = await async_playwright().start()
        # Connect to existing Chrome instance via CDP
        self.browser = await self.playwright.chromium.connect_over_cdp(
            endpoint_url=self.debugging_url
        )

        # Get the first available context (default)
        contexts = self.browser.contexts
        if contexts:
            self.context = contexts[0]
        else:
            # Create a new context if none exist
            self.context = await self.browser.new_context()

        # Get the active page
        pages = self.context.pages
        if pages:
            self.page = pages[0]
        else:
            self.page = await self.context.new_page()

        self._initialized = True

    async def get_active_page(self) -> Page:
        """Get the current active page, checking visibility and connection state"""
        if not self._initialized:
            await self.initialize()

        if not self.context or not self.context.pages:
            raise BrowserUnavailableError("No active context available")

        target_page = None
        
        # Try to find a visible page first (usually the active tab)
        for page in reversed(self.context.pages):
            try:
                if not page.is_closed():
                    is_visible = await page.evaluate("document.visibilityState === 'visible'")
                    if is_visible:
                        target_page = page
                        break
            except Exception:
                continue
                
        # Fallback to the last open page if visibility check fails
        if not target_page:
            for page in reversed(self.context.pages):
                if not page.is_closed():
                    target_page = page
                    break

        if not target_page:
            self._initialized = False  # Force reconnect on next try
            raise NoActivePageError("No active pages found.")

        if target_page.is_closed():
             raise PageClosedError("Active page is closed")

        return target_page

    async def execute_js(self, script: str):
        """Execute JavaScript on the active page"""
        target_page = await self.get_active_page()
        return await target_page.evaluate(script)

    async def execute_compiled(self, compiled_feature: "CompiledFeature"):
        """Execute pre-compiled JavaScript Feature"""
        return await self.execute_js(compiled_feature.javascript)

    async def cleanup(self):
        """Clean up resources"""
        if self.playwright:
            await self.playwright.stop()
        self._initialized = False