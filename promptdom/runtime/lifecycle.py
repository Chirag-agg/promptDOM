from typing import Optional
from .models import RuntimeFeature, FeatureState
from .registry import RuntimeRegistry
from ..compiler.models import CompiledFeature
from ..browser import BrowserManager
from ..analytics.collector import AnalyticsCollector
from ..analytics.models import RuntimeEventLog

class LifecycleManager:
    def __init__(self, registry: RuntimeRegistry, browser: BrowserManager, analytics: AnalyticsCollector):
        self.registry = registry
        self.browser = browser
        self.analytics = analytics

    def wrap_javascript(self, compiled: CompiledFeature, instance_id: str, feature_id: str) -> str:
        # Wrap pure JS with lifecycle bindings
        return f"""
        (function() {{
            window.__promptdom = window.__promptdom || {{}};
            window.__promptdom.features = window.__promptdom.features || {{}};
            
            const instanceId = "{instance_id}";
            const featureId = "{feature_id}";
            
            window.__promptdom.features[instanceId] = {{
                feature_id: featureId,
                started_at: Date.now(),
                heartbeat: Date.now(),
                state: "running"
            }};

            const hb_{instance_id.replace('-', '_')} = setInterval(() => {{
                if (window.__promptdom.features[instanceId]) {{
                    window.__promptdom.features[instanceId].heartbeat = Date.now();
                }} else {{
                    clearInterval(hb_{instance_id.replace('-', '_')});
                }}
            }}, 30000);
            
            try {{
                {compiled.javascript}
            }} catch (e) {{
                if (window.__promptdom.features[instanceId]) {{
                    window.__promptdom.features[instanceId].state = "failed";
                    window.__promptdom.features[instanceId].error = e.toString();
                }}
                throw e;
            }}
        }})();
        """

    async def install_and_run(self, compiled: CompiledFeature, feature_id: str) -> RuntimeFeature:
        instance = RuntimeFeature(feature_id=feature_id)
        self.registry.register(instance)
        
        wrapped_js = self.wrap_javascript(compiled, instance.runtime_instance_id, feature_id)
        
        try:
            await self.browser.execute_js(wrapped_js)
            self.registry.update_state(instance.runtime_instance_id, FeatureState.RUNNING)
            self.analytics.log_runtime_event(RuntimeEventLog(
                feature_id=feature_id,
                runtime_instance_id=instance.runtime_instance_id,
                event="STARTED"
            ))
            return instance
        except Exception as e:
            self.registry.update_state(instance.runtime_instance_id, FeatureState.FAILED, error=str(e))
            self.analytics.log_runtime_event(RuntimeEventLog(
                feature_id=feature_id,
                runtime_instance_id=instance.runtime_instance_id,
                event="FAILED"
            ))
            raise e
