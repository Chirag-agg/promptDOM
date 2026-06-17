from promptdom.runtime.registry import RuntimeRegistry
from promptdom.runtime.models import RuntimeFeature, FeatureState

def test_registry_register():
    registry = RuntimeRegistry()
    f = RuntimeFeature(feature_id="f1")
    registry.register(f)
    
    assert registry.get(f.runtime_instance_id) == f
    assert registry.get_by_feature_id("f1") == [f]
    assert len(registry.list_all()) == 1

def test_registry_update_state():
    registry = RuntimeRegistry()
    f = RuntimeFeature(feature_id="f1")
    registry.register(f)
    
    registry.update_state(f.runtime_instance_id, FeatureState.RUNNING, heartbeat=12345)
    
    f2 = registry.get(f.runtime_instance_id)
    assert f2.state == FeatureState.RUNNING
    assert f2.last_heartbeat == 12345

def test_registry_remove():
    registry = RuntimeRegistry()
    f = RuntimeFeature(feature_id="f1")
    registry.register(f)
    
    registry.remove(f.runtime_instance_id)
    assert registry.get(f.runtime_instance_id).state == FeatureState.REMOVED
