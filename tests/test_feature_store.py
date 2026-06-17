import pytest
import os
import json
from promptdom.features.models import Feature
from promptdom.features.store import FeatureStore

@pytest.fixture
def tmp_store(tmp_path):
    store_file = tmp_path / "data" / "features.json"
    return FeatureStore(data_file=str(store_file))

def test_store_creates_file_if_missing(tmp_path):
    store_file = tmp_path / "data" / "features.json"
    assert not os.path.exists(store_file)
    store = FeatureStore(data_file=str(store_file))
    assert os.path.exists(store_file)
    with open(store_file, "r") as f:
        assert json.load(f) == []

def test_store_create_and_get(tmp_store):
    f = Feature(
        name="test", prompt="hide something", source="manual",
        hostname="example.com", page_type="test", target="something",
        target_type="section", action="hide", selector=".thing"
    )
    tmp_store.create_feature(f)
    retrieved = tmp_store.get_feature(f.id)
    assert retrieved is not None
    assert retrieved.name == "test"

def test_store_list(tmp_store):
    f1 = Feature(name="t1", prompt="p1", source="manual", hostname="ex.com", page_type="t", target="t", target_type="s", action="hide", selector=".1")
    f2 = Feature(name="t2", prompt="p2", source="manual", hostname="ex.com", page_type="t", target="t", target_type="s", action="hide", selector=".2")
    tmp_store.create_feature(f1)
    tmp_store.create_feature(f2)
    features = tmp_store.list_features()
    assert len(features) == 2

def test_store_update(tmp_store):
    f = Feature(name="test", prompt="p1", source="manual", hostname="ex.com", page_type="t", target="t", target_type="s", action="hide", selector=".1")
    tmp_store.create_feature(f)
    updated = tmp_store.update_feature(f.id, {"name": "updated"})
    assert updated.name == "updated"
    assert tmp_store.get_feature(f.id).name == "updated"

def test_store_toggle(tmp_store):
    f = Feature(name="test", prompt="p1", source="manual", hostname="ex.com", page_type="t", target="t", target_type="s", action="hide", selector=".1")
    tmp_store.create_feature(f)
    assert f.enabled is True
    toggled = tmp_store.toggle_feature(f.id)
    assert toggled.enabled is False
    toggled = tmp_store.toggle_feature(f.id)
    assert toggled.enabled is True

def test_store_delete(tmp_store):
    f = Feature(name="test", prompt="p1", source="manual", hostname="ex.com", page_type="t", target="t", target_type="s", action="hide", selector=".1")
    tmp_store.create_feature(f)
    assert tmp_store.delete_feature(f.id) is True
    assert tmp_store.get_feature(f.id) is None
    assert tmp_store.delete_feature(f.id) is False

def test_store_corrupted_file(tmp_store):
    with open(tmp_store.data_file, "w") as f:
        f.write("corrupted json")
    features = tmp_store.list_features()
    assert features == []
