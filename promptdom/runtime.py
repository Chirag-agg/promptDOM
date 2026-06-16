from typing import Optional



class RuntimeEngine:
    def __init__(self):
        pass

    def _generate_hide_js(self, selector: str) -> str:
        """Generate JavaScript to hide elements"""
        return f"""
        (() => {{
            const elements = document.querySelectorAll('{selector}');
            elements.forEach(el => {{
                el.style.display = 'none';
                // Store original display for potential restore
                el.setAttribute('data-original-display', el.style.display || getComputedStyle(el).display);
            }});
        }})()
        """

    def _generate_show_js(self, selector: str) -> str:
        """Generate JavaScript to show elements"""
        return f"""
        (() => {{
            const elements = document.querySelectorAll('{selector}');
            elements.forEach(el => {{
                const originalDisplay = el.getAttribute('data-original-display');
                if (originalDisplay) {{
                    el.style.display = originalDisplay;
                }} else {{
                    el.style.display = '';
                }}
            }});
        }})()
        """

    def _generate_highlight_js(self, selector: str) -> str:
        """Generate JavaScript to highlight elements"""
        return f"""
        (() => {{
            const elements = document.querySelectorAll('{selector}');
            elements.forEach(el => {{
                el.style.border = '3px solid yellow';
                el.style.borderRadius = '4px';
                el.style.boxShadow = '0 0 10px rgba(255, 255, 0, 0.5)';
                // Store original styles for potential restore
                el.setAttribute('data-original-border', el.style.border || '');
                el.setAttribute('data-original-box-shadow', el.style.boxShadow || '');
            }});
        }})()
        """

    def _generate_unhighlight_js(self, selector: str) -> str:
        """Generate JavaScript to remove highlight from elements"""
        return f"""
        (() => {{
            const elements = document.querySelectorAll('{selector}');
            elements.forEach(el => {{
                const originalBorder = el.getAttribute('data-original-border') || '';
                const originalBoxShadow = el.getAttribute('data-original-box-shadow') || '';
                el.style.border = originalBorder;
                el.style.boxShadow = originalBoxShadow;
                el.removeAttribute('data-original-border');
                el.removeAttribute('data-original-box-shadow');
            }});
        }})()
        """

    async def execute(self, action: str, selector: str, browser_manager) -> bool:
        """
        Execute a feature action
        Returns True if successful
        """
        if not selector:
            raise ValueError("Selector cannot be empty")

        js_script = None

        if action == "hide":
            js_script = self._generate_hide_js(selector)
        elif action == "show":
            js_script = self._generate_show_js(selector)
        elif action == "highlight":
            js_script = self._generate_highlight_js(selector)
        elif action == "unhighlight":
            js_script = self._generate_unhighlight_js(selector)
        else:
            raise ValueError(f"Unknown action: {action}")

        await browser_manager.execute_js(js_script)
        return True