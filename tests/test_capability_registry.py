from promptdom.capabilities.registry import CapabilityRegistry
from promptdom.capabilities.models import CapabilityID, ExecutorType

def test_capability_registry_builtins():
    registry = CapabilityRegistry()
    
    assert registry.is_supported(CapabilityID.DOM_MANIPULATION) is True
    assert registry.is_supported(CapabilityID.OBSERVE) is True
    assert registry.is_supported(CapabilityID.NOTIFICATIONS) is True
    
    cap = registry.get(CapabilityID.NOTIFICATIONS)
    assert cap.executor == ExecutorType.JAVASCRIPT
    assert cap.requires_permission is True

def test_capability_registry_list_all():
    registry = CapabilityRegistry()
    caps = registry.list_all()
    
    assert "DOM_MANIPULATION" in caps
    assert caps["DOM_MANIPULATION"] is True
    assert "NOTIFICATIONS" in caps
    assert caps["NOTIFICATIONS"] is True
