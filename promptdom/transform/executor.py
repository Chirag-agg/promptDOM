import re
from ..browser import BrowserManager

def strip_markdown_blocks(text: str) -> str:
    """Removes ```css ... ``` or ```javascript ... ``` wrappers from LLM output."""
    if not text:
        return text
    # Remove start blocks
    text = re.sub(r'^```[a-zA-Z]*\n', '', text.strip())
    # Remove end blocks
    text = re.sub(r'\n```$', '', text.strip())
    return text.strip()

class TransformExecutor:
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    async def apply_css(self, transformation_id: str, css: str) -> bool:
        css = strip_markdown_blocks(css)
        if not css:
            return False
            
        script = f"""
        (() => {{
            const id = 'promptdom-transform-{transformation_id}';
            let style = document.getElementById(id);
            if (!style) {{
                style = document.createElement('style');
                style.id = id;
                style.setAttribute('data-promptdom-id', '{transformation_id}');
                document.head.appendChild(style);
            }}
            style.textContent = `{css.replace('`', '\\`').replace('$', '\\$')}`;
        }})();
        """
        try:
            await self.browser.execute_js(script)
            return True
        except Exception as e:
            print(f"Error applying CSS: {e}")
            return False

    async def apply_javascript(self, transformation_id: str, javascript: str) -> bool:
        javascript = strip_markdown_blocks(javascript)
        if not javascript:
            return False
            
        script = f"""
        (() => {{
            try {{
                {javascript}
            }} catch (e) {{
                console.error("[PromptDOM Transform Error]", e);
            }}
        }})();
        """
        try:
            await self.browser.execute_js(script)
            return True
        except Exception as e:
            print(f"Error applying JS: {e}")
            return False

    async def remove_transformation(self, transformation_id: str) -> bool:
        script = f"""
        (() => {{
            const style = document.getElementById('promptdom-transform-{transformation_id}');
            if (style) {{
                style.remove();
            }}
        }})();
        """
        try:
            await self.browser.execute_js(script)
            return True
        except Exception as e:
            print(f"Error removing transformation: {e}")
            return False
