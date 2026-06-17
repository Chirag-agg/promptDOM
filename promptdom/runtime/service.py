from typing import List, Optional
import time
from .registry import RuntimeRegistry
from .models import RuntimeFeature, FeatureState
from .lifecycle import LifecycleManager
from ..compiler.compiler import FeatureCompiler
from ..compiler.models import FeatureSpec
from ..features.store import FeatureStore
from ..analytics.collector import AnalyticsCollector
from ..analytics.models import RuntimeEventLog
from ..browser import BrowserManager

class RuntimeService:
    def __init__(self, registry: RuntimeRegistry, lifecycle: LifecycleManager, compiler: FeatureCompiler, store: FeatureStore, analytics: AnalyticsCollector, browser: BrowserManager):
        self.registry = registry
        self.lifecycle = lifecycle
        self.compiler = compiler
        self.store = store
        self.analytics = analytics
        self.browser = browser

    def get_all_features(self) -> List[RuntimeFeature]:
        return self.registry.list_all()

    async def stop_feature(self, instance_id: str) -> bool:
        feature = self.registry.get(instance_id)
        if not feature or feature.state in [FeatureState.STOPPED, FeatureState.REMOVED]:
            return False

        # Attempt to remove from DOM state
        try:
            await self.browser.execute_js(f'delete window.__promptdom?.features["{instance_id}"];')
        except Exception:
            pass # ignore if browser is disconnected

        self.registry.update_state(instance_id, FeatureState.STOPPED)
        self.analytics.log_runtime_event(RuntimeEventLog(
            feature_id=feature.feature_id,
            runtime_instance_id=instance_id,
            event="STOPPED"
        ))
        return True

    async def restart_feature(self, instance_id: str) -> Optional[RuntimeFeature]:
        feature = self.registry.get(instance_id)
        if not feature:
            return None

        # Stop existing
        await self.stop_feature(instance_id)

        # Get feature definition
        stored_feature = self.store.get_feature(feature.feature_id)
        if not stored_feature or not stored_feature.feature_spec:
            raise ValueError(f"Feature {feature.feature_id} has no stored spec")

        from pydantic import TypeAdapter
        adapter = TypeAdapter(FeatureSpec)
        spec = adapter.validate_python(stored_feature.feature_spec)

        compiled = self.compiler.compile(spec)
        new_instance = await self.lifecycle.install_and_run(compiled, feature.feature_id)
        return new_instance

    def cleanup_dead_features(self, timeout_ms: int = 60000) -> int:
        now = int(time.time() * 1000)
        cleaned_count = 0
        for feature in self.registry.list_by_state(FeatureState.RUNNING):
            if feature.last_heartbeat is not None and (now - feature.last_heartbeat) > timeout_ms:
                self.registry.update_state(feature.runtime_instance_id, FeatureState.STOPPED, error="Heartbeat timeout")
                self.analytics.log_runtime_event(RuntimeEventLog(
                    feature_id=feature.feature_id,
                    runtime_instance_id=feature.runtime_instance_id,
                    event="STOPPED"
                ))
                cleaned_count += 1
        return cleaned_count
