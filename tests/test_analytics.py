import os
import tempfile
import pytest
from promptdom.analytics.collector import AnalyticsCollector
from promptdom.analytics.models import ApplicationLog, RepairLog
from promptdom.analytics.service import AnalyticsService
from promptdom.features.models import Feature
from unittest.mock import MagicMock

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as d:
        yield d

@pytest.fixture
def collector(temp_dir):
    return AnalyticsCollector(data_dir=temp_dir)

def test_collector_append(collector):
    app_log = ApplicationLog(feature_id="f1", success=True, execution_time_ms=10.0, page_url="http://test.com")
    collector.log_application(app_log)
    
    rep_log = RepairLog(feature_id="f1", old_selector="old", new_selector="new", confidence=0.9, repair_method="test")
    collector.log_repair(rep_log)
    
    apps = collector.get_application_logs()
    reps = collector.get_repair_logs()
    
    assert len(apps) == 1
    assert apps[0].feature_id == "f1"
    
    assert len(reps) == 1
    assert reps[0].new_selector == "new"

def test_analytics_service_feature_decay(collector):
    # Log 3 repairs for f1
    for _ in range(3):
        collector.log_repair(RepairLog(feature_id="f1", old_selector="o", new_selector="n", confidence=0.9, repair_method="t"))
        
    # Log 2 apps for f1
    collector.log_application(ApplicationLog(feature_id="f1", success=True, execution_time_ms=10.0, page_url="a"))
    collector.log_application(ApplicationLog(feature_id="f1", success=False, execution_time_ms=5.0, page_url="a"))
    
    store = MagicMock()
    # Age is basically 0 days -> rounded to 1 day by `max(1.0, ...)`
    f1 = Feature(name="f1", prompt="p", source="m", hostname="t", page_type="p", target="t", target_type="t", action="a", selector="s", repair_count=3)
    f1.id = "f1"
    store.list_features.return_value = [f1]
    
    service = AnalyticsService(store, collector)
    features = service.get_feature_analytics()
    
    assert len(features) == 1
    f = features[0]
    assert f.apply_count == 2
    assert f.success_rate == 0.5
    assert f.average_execution_ms == 10.0  # (only successful counted for avg time)
    assert f.feature_decay_score == 3.0  # 3 repairs / 1 day

def test_site_analytics(collector):
    store = MagicMock()
    f1 = Feature(name="f1", prompt="p", source="m", hostname="youtube.com", page_type="p", target="t", target_type="t", action="a", selector="s")
    f1.last_status = "stale"
    f2 = Feature(name="f2", prompt="p", source="m", hostname="youtube.com", page_type="p", target="t", target_type="t", action="a", selector="s")
    f2.last_status = "ready"
    
    store.list_features.return_value = [f1, f2]
    service = AnalyticsService(store, collector)
    
    sites = service.get_site_analytics()
    assert len(sites) == 1
    assert sites[0].hostname == "youtube.com"
    assert sites[0].feature_count == 2
    assert sites[0].stale_features == 1
