from ..browser import BrowserManager

class TransformExecutor:
    def __init__(self, browser: BrowserManager):
        self.browser = browser

    async def apply_css(self, transformation_id: str, css: str) -> bool:
        if not css or not css.strip():
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
        if not javascript or not javascript.strip():
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
