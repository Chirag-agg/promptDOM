import asyncio
import time
from .registry import RuntimeRegistry
from .models import FeatureState
from .service import RuntimeService
from ..browser import BrowserManager

class HeartbeatMonitor:
    def __init__(self, browser: BrowserManager, registry: RuntimeRegistry, service: RuntimeService, poll_interval_sec: int = 15):
        self.browser = browser
        self.registry = registry
        self.service = service
        self.poll_interval_sec = poll_interval_sec
        self._task = None
        self._running = False

    def start(self):
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _loop(self):
        while self._running:
            await asyncio.sleep(self.poll_interval_sec)
            try:
                await self._check_heartbeats()
                self.service.cleanup_dead_features()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Heartbeat monitor error: {e}")

    async def _check_heartbeats(self):
        if not self.browser.page:
            return

        try:
            # Poll window.__promptdom.features
            state = await self.browser.execute_js("return window.__promptdom?.features || {};")
            
            # Sync registry with browser state
            for instance_id, data in state.items():
                if instance_id in self.registry._features:
                    heartbeat = data.get("heartbeat")
                    feature_state = data.get("state")
                    if heartbeat:
                        # Update the heartbeat timestamp in registry
                        self.registry.update_state(instance_id, FeatureState.RUNNING, heartbeat=heartbeat)
                    
                    if feature_state == "failed":
                        self.registry.update_state(instance_id, FeatureState.FAILED, error=data.get("error"))

        except Exception as e:
            # Browser might be disconnected or evaluating failed
            pass
