from typing import Dict
from .models import Capability, CapabilityID, ExecutorType

class CapabilityRegistry:
    def __init__(self):
        self._capabilities: Dict[CapabilityID, Capability] = {}
        self._initialize_builtins()

    def _initialize_builtins(self):
        self.register(Capability(
            id=CapabilityID.DOM_MANIPULATION,
            name="DOM Manipulation",
            supported=True,
            executor=ExecutorType.JAVASCRIPT
        ))
        
        self.register(Capability(
            id=CapabilityID.OBSERVE,
            name="DOM Observation",
            supported=True,
            executor=ExecutorType.JAVASCRIPT
        ))
        
        self.register(Capability(
            id=CapabilityID.NOTIFICATIONS,
            name="Browser Notifications",
            supported=True,
            executor=ExecutorType.JAVASCRIPT,
            requires_permission=True
        ))

    def register(self, capability: Capability) -> None:
        self._capabilities[capability.id] = capability

    def get(self, capability_id: CapabilityID) -> Capability:
        return self._capabilities.get(capability_id)

    def is_supported(self, capability_id: CapabilityID) -> bool:
        cap = self.get(capability_id)
        return cap.supported if cap else False

    def list_all(self) -> Dict[str, bool]:
        """Returns a simple dictionary mapping capability ID to its supported status"""
        return {cap.id.value: cap.supported for cap in self._capabilities.values()}
