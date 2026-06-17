import pytest
from unittest.mock import AsyncMock, MagicMock
from promptdom.features.auto_apply import AutoApplyService, AppliedFeatureCache
from promptdom.features.matching_models import MatchResult, FeatureMatch
from promptdom.features.models import Feature
from promptdom.inspection.models import InspectionResponse, DOMSummary

@pytest.fixture
def mock_deps():
    matching_service = MagicMock()
    matching_service.get_matches = AsyncMock()
    
    store = MagicMock()
    
    runtime = MagicMock()
    runtime.execute = AsyncMock(return_value=True)
    
    inspection_service = MagicMock()
    inspection_service.inspect = AsyncMock()
    inspection_service.inspect.return_value = InspectionResponse(
        url="http://test.com", hostname="test.com", title="Test", page_type="test", dom_fingerprint="fingerprint1",
        headings=[], buttons=[], inputs=[], links=[], sections=[], interactive_elements=[], visible_text_sample="", summary=DOMSummary(heading_count=0, button_count=0, input_count=0, link_count=0, section_count=0, visible_text_length=0)
    )
    
    browser_manager = MagicMock()
    browser_manager.get_active_tab_info = AsyncMock(return_value={"url": "http://test.com"})
    
    analytics_collector = MagicMock()
    
    return matching_service, store, runtime, inspection_service, browser_manager, analytics_collector

@pytest.mark.asyncio
async def test_cache_logic():
    cache = AppliedFeatureCache()
    assert not cache.has_applied("f1", "url1", "fp1")
    cache.mark_applied("f1", "url1", "fp1")
    assert cache.has_applied("f1", "url1", "fp1")
    # Different url
    assert not cache.has_applied("f1", "url2", "fp1")
    # Different fingerprint
    assert not cache.has_applied("f1", "url1", "fp2")

@pytest.mark.asyncio
async def test_auto_apply_skips_non_ready(mock_deps):
    matching, store, runtime, inspection, browser, collector = mock_deps
    
    matching.get_matches.return_value = MatchResult(
        page_hostname="test.com", page_type="test",
        matches=[
            FeatureMatch(feature_id="f1", feature_name="f1", confidence=0.0, feature_health=1.0, status="disabled", reason=""),
            FeatureMatch(feature_id="f2", feature_name="f2", confidence=0.5, feature_health=0.0, status="stale", reason=""),
            FeatureMatch(feature_id="f3", feature_name="f3", confidence=0.8, feature_health=1.0, status="partial", reason="")
        ]
    )
    
    service = AutoApplyService(matching, store, runtime, inspection, browser, collector)
    result = await service.apply_features()
    
    assert result.total_matches == 3
    assert result.applied_count == 0
    assert result.skipped_count == 3
    assert result.failed_count == 0
    assert len(result.results) == 0
    runtime.execute.assert_not_called()

@pytest.mark.asyncio
async def test_auto_apply_executes_ready(mock_deps):
    matching, store, runtime, inspection, browser, collector = mock_deps
    
    matching.get_matches.return_value = MatchResult(
        page_hostname="test.com", page_type="test",
        matches=[
            FeatureMatch(feature_id="f1", feature_name="f1", confidence=1.0, feature_health=1.0, status="ready", reason="")
        ]
    )
    
    f1 = Feature(name="f1", prompt="p", source="m", hostname="test.com", page_type="test", target="t", target_type="s", action="hide", selector=".sel")
    f1.id = "f1"
    store.get_feature.return_value = f1
    
    service = AutoApplyService(matching, store, runtime, inspection, browser, collector)
    result = await service.apply_features()
    
    assert result.total_matches == 1
    assert result.applied_count == 1
    assert result.skipped_count == 0
    assert result.failed_count == 0
    assert len(result.results) == 1
    
    runtime.execute.assert_called_once_with("hide", ".sel", browser)
    
    # Second run should skip due to cache
    result2 = await service.apply_features()
    assert result2.skipped_count == 1
    assert runtime.execute.call_count == 1

@pytest.mark.asyncio
async def test_auto_apply_dry_run(mock_deps):
    matching, store, runtime, inspection, browser, collector = mock_deps
    
    matching.get_matches.return_value = MatchResult(
        page_hostname="test.com", page_type="test",
        matches=[
            FeatureMatch(feature_id="f1", feature_name="f1", confidence=1.0, feature_health=1.0, status="ready", reason="")
        ]
    )
    
    f1 = Feature(name="f1", prompt="p", source="m", hostname="test.com", page_type="test", target="t", target_type="s", action="hide", selector=".sel")
    f1.id = "f1"
    store.get_feature.return_value = f1
    
    service = AutoApplyService(matching, store, runtime, inspection, browser, collector)
    result = await service.apply_features(dry_run=True)
    
    assert result.applied_count == 1
    assert result.results[0].message == "Dry run: would execute"
    runtime.execute.assert_not_called()
