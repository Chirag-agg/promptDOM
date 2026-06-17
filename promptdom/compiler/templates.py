class TemplateRegistry:
    TEMPLATES = {
        "hide_element": """
        {{
            const elements = document.querySelectorAll(`{selector}`);
            elements.forEach(el => {{
                el.style.display = 'none';
            }});
        }}
        """,
        "show_element": """
        {{
            const elements = document.querySelectorAll(`{selector}`);
            elements.forEach(el => {{
                el.style.display = '';
            }});
        }}
        """,
        "highlight_element": """
        {{
            const elements = document.querySelectorAll(`{selector}`);
            elements.forEach(el => {{
                el.style.backgroundColor = 'yellow';
                el.style.border = '2px solid red';
            }});
        }}
        """,
        "monitor_element": """
        {{
            const selector = `{selector}`;
            if (!window._promptdom_monitors) {{
                window._promptdom_monitors = {{}};
            }}
            if (!window._promptdom_monitors[selector]) {{
                const observer = new MutationObserver((mutations) => {{
                    const el = document.querySelector(selector);
                    if (el) {{
                        el.setAttribute('data-promptdom-monitored', 'true');
                    }}
                }});
                observer.observe(document.body, {{ childList: true, subtree: true }});
                window._promptdom_monitors[selector] = observer;
                
                // initial check
                const el = document.querySelector(selector);
                if (el) {{
                    el.setAttribute('data-promptdom-monitored', 'true');
                }}
            }}
        }}
        """,
        "periodic_task": """
        {{
            const interval = {interval_ms};
            const operation = `{operation}`;
            
            if (!window._promptdom_tasks) {{
                window._promptdom_tasks = {{}};
            }}
            
            if (window._promptdom_tasks[operation]) {{
                clearInterval(window._promptdom_tasks[operation]);
            }}
            
            window._promptdom_tasks[operation] = setInterval(() => {{
                console.log('Running promptDOM task:', operation);
            }}, interval);
        }}
        """,
        "text_match_highlight": """
        {{
            const elements = document.querySelectorAll(`{selector}`);
            const pattern = new RegExp(`{pattern}`, 'gi');
            elements.forEach(el => {{
                if (pattern.test(el.textContent)) {{
                    el.style.backgroundColor = 'yellow';
                }}
            }});
        }}
        """,
        "notify": """
        {{
            if (Notification.permission === 'granted') {{
                new Notification(`{title}`, {{ body: `{message}` }});
            }} else {{
                console.warn('PromptDOM: NotifyAction failed, permission not granted.');
            }}
        }}
        """,
        "observe_element": """
        {{
            const selector = `{selector}`;
            const event = `{event}`;
            const observer = new MutationObserver((mutations) => {{
                mutations.forEach(mutation => {{
                    if (event === 'ELEMENT_ADDED' && mutation.addedNodes.length > 0) {{
                        // Very naive check for the selector
                        if (document.querySelector(selector)) {{
                            console.log('ObserveElement trigger: ELEMENT_ADDED for', selector);
                        }}
                    }} else if (event === 'ELEMENT_REMOVED' && mutation.removedNodes.length > 0) {{
                        if (!document.querySelector(selector)) {{
                            console.log('ObserveElement trigger: ELEMENT_REMOVED for', selector);
                        }}
                    }} else if (event === 'TEXT_CHANGED' && mutation.type === 'characterData') {{
                        console.log('ObserveElement trigger: TEXT_CHANGED for', selector);
                    }}
                }});
            }});
            observer.observe(document.body, {{ childList: true, subtree: true, characterData: true }});
            
            // Store observer on window to be cleaned up if needed
            window.__promptdom = window.__promptdom || {{}};
            window.__promptdom.observers = window.__promptdom.observers || {{}};
            window.__promptdom.observers[`{action_id}`] = observer;
        }}
        """
    }

    @classmethod
    def get_template(cls, operation: str) -> str:
        if operation not in cls.TEMPLATES:
            raise ValueError(f"No template found for operation: {operation}")
        return cls.TEMPLATES[operation]
