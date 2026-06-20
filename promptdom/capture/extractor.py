from html.parser import HTMLParser
from io import StringIO

from ..browser import BrowserManager
from .models import SemanticElement, LayoutElement


class _DOMCleaner(HTMLParser):
    """Strips <script>, <style>, <svg>, <noscript> and their contents from HTML."""

    REMOVE_TAGS = frozenset({"script", "style", "svg", "noscript"})

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._output = StringIO()
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self.REMOVE_TAGS:
            self._skip_depth += 1
            return
        if self._skip_depth > 0:
            return
        attr_str = ""
        for name, value in attrs:
            if value is None:
                attr_str += f" {name}"
            else:
                # Escape double quotes in attribute values
                escaped = value.replace("&", "&amp;").replace('"', "&quot;")
                attr_str += f' {name}="{escaped}"'
        self._output.write(f"<{tag}{attr_str}>")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.REMOVE_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
            return
        if self._skip_depth > 0:
            return
        self._output.write(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        self._output.write(data)

    def handle_entityref(self, name: str) -> None:
        if self._skip_depth > 0:
            return
        self._output.write(f"&{name};")

    def handle_charref(self, name: str) -> None:
        if self._skip_depth > 0:
            return
        self._output.write(f"&#{name};")

    def handle_comment(self, data: str) -> None:
        # Strip comments entirely
        pass

    def get_output(self) -> str:
        return self._output.getvalue()


def clean_dom(raw_html: str) -> str:
    """Remove script/style/svg/noscript from HTML, preserving semantic structure."""
    cleaner = _DOMCleaner()
    cleaner.feed(raw_html)
    return cleaner.get_output()


# ---------------------------------------------------------------------------
# Browser-side JavaScript
# ---------------------------------------------------------------------------

_SEMANTIC_JS = """
() => {
    const norm = (s) => s ? s.trim().replace(/\\s+/g, ' ') : null;

    // Generate stable CSS path (identical to inspection/extractor.py)
    const getCssPath = (el) => {
        if (!(el instanceof Element)) return '';
        const path = [];
        while (el.nodeType === Node.ELEMENT_NODE) {
            let selector = el.nodeName.toLowerCase();
            if (el.id) {
                selector += '#' + el.id;
                path.unshift(selector);
                break;
            } else {
                let sib = el, nth = 1;
                while (sib = sib.previousElementSibling) {
                    if (sib.nodeName.toLowerCase() === selector)
                        nth++;
                }
                if (nth !== 1) selector += ':nth-of-type(' + nth + ')';
            }
            path.unshift(selector);
            el = el.parentNode;
        }
        return path.join(' > ');
    };

    const isVisible = (el) => el.offsetWidth > 0 && el.offsetHeight > 0;

    const seen = new Set();
    const elements = [];

    const collect = (nodeList) => {
        for (const el of nodeList) {
            if (!isVisible(el)) continue;
            const path = getCssPath(el);
            if (!path || seen.has(path)) continue;
            seen.add(path);
            elements.push({
                tag: el.tagName.toLowerCase(),
                text: norm(el.innerText || el.value || el.placeholder || el.title || el.getAttribute('aria-label')),
                aria_label: norm(el.getAttribute('aria-label')),
                role: el.getAttribute('role') || null,
                selector: path
            });
        }
    };

    // Buttons
    collect(document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]'));
    // Links
    collect(document.querySelectorAll('a[href], [role="link"]'));
    // Inputs
    collect(document.querySelectorAll('input:not([type="button"]):not([type="submit"]), textarea, select'));
    // Headings
    collect(document.querySelectorAll('h1, h2, h3, h4, h5, h6'));
    // ARIA roles not already captured
    collect(document.querySelectorAll('[role]:not(button):not(a):not(input):not(textarea):not(select):not(h1):not(h2):not(h3):not(h4):not(h5):not(h6)'));

    return {
        url: window.location.href,
        title: document.title,
        elements: elements
    };
}
"""

_LAYOUT_JS = """
() => {
    const MAX = 500;

    const getCssPath = (el) => {
        if (!(el instanceof Element)) return '';
        const path = [];
        while (el.nodeType === Node.ELEMENT_NODE) {
            let selector = el.nodeName.toLowerCase();
            if (el.id) {
                selector += '#' + el.id;
                path.unshift(selector);
                break;
            } else {
                let sib = el, nth = 1;
                while (sib = sib.previousElementSibling) {
                    if (sib.nodeName.toLowerCase() === selector)
                        nth++;
                }
                if (nth !== 1) selector += ':nth-of-type(' + nth + ')';
            }
            path.unshift(selector);
            el = el.parentNode;
        }
        return path.join(' > ');
    };

    const selector = 'button, a, input, textarea, select, ' +
        'h1, h2, h3, h4, h5, h6, ' +
        '[role="button"], [role="link"], [role="tab"], [role="menuitem"], ' +
        'img, nav, header, footer, main, section, aside';

    const nodes = document.querySelectorAll(selector);
    const results = [];
    const seen = new Set();

    for (let i = 0; i < nodes.length && results.length < MAX; i++) {
        const el = nodes[i];
        const path = getCssPath(el);
        if (!path || seen.has(path)) continue;
        seen.add(path);

        const rect = el.getBoundingClientRect();
        const visible = el.offsetWidth > 0 && el.offsetHeight > 0;

        results.push({
            selector: path,
            x: rect.x,
            y: rect.y,
            width: rect.width,
            height: rect.height,
            visible: visible
        });
    }

    return results;
}
"""


class SiteExtractor:
    """Extracts semantic elements, layout data, and cleaned DOM from any website."""

    def __init__(self, browser_manager: BrowserManager):
        self.browser_manager = browser_manager

    async def extract_semantic(self) -> tuple[str, str, list[SemanticElement]]:
        """
        Extract page URL, title, and semantic elements via browser-side JS.
        Returns (url, title, elements).
        """
        page = await self.browser_manager.get_active_page()
        raw = await page.evaluate(_SEMANTIC_JS)

        elements = [SemanticElement(**item) for item in raw["elements"]]
        return raw["url"], raw["title"], elements

    async def extract_layout(self) -> list[LayoutElement]:
        """
        Extract bounding-rect layout data for key visible elements.
        Returns list of LayoutElement records (capped at 500).
        """
        page = await self.browser_manager.get_active_page()
        raw = await page.evaluate(_LAYOUT_JS)

        return [LayoutElement(**item) for item in raw]

    async def extract_cleaned_dom(self) -> str:
        """
        Capture the full page HTML and return a cleaned version
        with script/style/svg/noscript removed.
        Intended for future LLM consumption.
        """
        page = await self.browser_manager.get_active_page()
        raw_html = await page.content()
        return clean_dom(raw_html)
