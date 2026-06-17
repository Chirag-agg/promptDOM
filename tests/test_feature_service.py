import pytest
from promptdom.features.models import FeatureCreate
from promptdom.features.service import FeatureService
from promptdom.features.store import FeatureStore

@pytest.fixture
def tmp_service(tmp_path):
    store_file = tmp_path / "data" / "features.json"
    return FeatureService(FeatureStore(data_file=str(store_file)))

def test_service_validation():
    with pytest.raises(ValueError):
        FeatureCreate(name="", prompt="p", source="s", hostname="h", page_type="p", target="t", target_type="t", action="a", selector="s")

def test_service_create(tmp_service):
    data = FeatureCreate(name="test", prompt="p1", source="manual", hostname="ex.com", page_type="t", target="t", target_type="s", action="hide", selector=".1")
    f = tmp_service.create_feature(data)
    assert f.id is not None
    assert f.created_at.endswith("Z")

def test_service_update_validation(tmp_service):
    data = FeatureCreate(name="test", prompt="p1", source="manual", hostname="ex.com", page_type="t", target="t", target_type="s", action="hide", selector=".1")
    f = tmp_service.create_feature(data)
    
    with pytest.raises(ValueError):
        tmp_service.update_feature(f.id, {"name": " "})
