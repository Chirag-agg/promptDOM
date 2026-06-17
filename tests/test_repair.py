import pytest
from unittest.mock import AsyncMock, MagicMock
from promptdom.features.models import Feature
from promptdom.repair.updater import SelectorVerifier
from promptdom.repair.service import FeatureRepairService
from promptdom.inspection.models import ResolutionInspectionResponse
from promptdom.resolution.models import ResolutionResult

@pytest.fixture
def mock_deps():
    store = MagicMock()
    
    inspection_service = MagicMock()
    inspection_service.inspect = AsyncMock()
    inspection_service.inspect.return_value.hostname = "test.com"
    inspection_service.inspect_resolution = AsyncMock()
    inspection_service.inspect_resolution.return_value = ResolutionInspectionResponse(
        dom_fingerprint="fp1",
        headings=[], buttons=[], inputs=[], links=[], sections=[], interactive_elements=[]
    )
    
    resolver = MagicMock()
    resolver.resolve = AsyncMock()
    
    verifier = MagicMock()
    verifier.get_alive_selectors = MagicMock(return_value={"#alive"})
    
    collector = MagicMock()
    
    return store, inspection_service, resolver, verifier, collector

@pytest.mark.asyncio
async def test_get_stale_features(mock_deps):
    store, inspection, resolver, verifier, collector = mock_deps
    
    f1 = Feature(name="f1", prompt="p", source="m", hostname="test.com", page_type="p", target="t", target_type="s", action="hide", selector="#alive")
    f2 = Feature(name="f2", prompt="p", source="m", hostname="test.com", page_type="p", target="t", target_type="s", action="hide", selector="#dead")
    f3 = Feature(name="f3", prompt="p", source="m", hostname="other.com", page_type="p", target="t", target_type="s", action="hide", selector="#dead")
    
    store.list_features.return_value = [f1, f2, f3]
    
    service = FeatureRepairService(store, inspection, resolver, verifier, collector)
    stale = await service.get_stale_features()
    
    assert len(stale) == 1
    assert stale[0].name == "f2"

@pytest.mark.asyncio
async def test_repair_features_success(mock_deps):
    store, inspection, resolver, verifier, collector = mock_deps
    
    f1 = Feature(name="f1", prompt="p", source="m", hostname="test.com", page_type="p", target="t", target_type="s", action="hide", selector="#dead")
    f1.id = "f1"
    store.list_features.return_value = [f1]
    
    resolver.resolve.return_value = ResolutionResult(matched=True, selector="#alive", confidence=0.9, explanation="", candidate_count=1, top_candidates=[])
    
    service = FeatureRepairService(store, inspection, resolver, verifier, collector)
    result = await service.repair_features(dry_run=False)
    
    assert result.repaired_count == 1
    assert result.failed_count == 0
    assert result.attempts[0].success is True
    
    store.update_feature.assert_called_once()
    updates = store.update_feature.call_args[0][1]
    assert updates["selector"] == "#alive"
    assert updates["repair_count"] == 1
    collector.log_repair.assert_called_once()

@pytest.mark.asyncio
async def test_repair_features_low_confidence(mock_deps):
    store, inspection, resolver, verifier, collector = mock_deps
    
    f1 = Feature(name="f1", prompt="p", source="m", hostname="test.com", page_type="p", target="t", target_type="s", action="hide", selector="#dead")
    store.list_features.return_value = [f1]
    
    resolver.resolve.return_value = ResolutionResult(matched=True, selector="#alive", confidence=0.8, explanation="", candidate_count=1, top_candidates=[])
    
    service = FeatureRepairService(store, inspection, resolver, verifier, collector)
    result = await service.repair_features()
    
    assert result.repaired_count == 0
    assert result.failed_count == 1
    assert "Confidence" in result.attempts[0].reason
    store.update_feature.assert_not_called()

@pytest.mark.asyncio
async def test_repair_features_missing_selector(mock_deps):
    store, inspection, resolver, verifier, collector = mock_deps
    
    f1 = Feature(name="f1", prompt="p", source="m", hostname="test.com", page_type="p", target="t", target_type="s", action="hide", selector="#dead")
    store.list_features.return_value = [f1]
    
    # Resolver returns a selector that is not in `alive_selectors`
    resolver.resolve.return_value = ResolutionResult(matched=True, selector="#ghost", confidence=0.9, explanation="", candidate_count=1, top_candidates=[])
    
    service = FeatureRepairService(store, inspection, resolver, verifier, collector)
    result = await service.repair_features()
    
    assert result.repaired_count == 0
    assert result.failed_count == 1
    assert "active DOM" in result.attempts[0].reason
    store.update_feature.assert_not_called()


