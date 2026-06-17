import pytest
from unittest.mock import AsyncMock, MagicMock
from promptdom.features.matcher import FeatureMatcher
from promptdom.features.models import Feature
from promptdom.resolution.models import ResolutionResult

@pytest.fixture
def mock_resolver():
    resolver = MagicMock()
    resolver.resolve = AsyncMock()
    return resolver

@pytest.mark.asyncio
async def test_matcher_disabled_feature(mock_resolver):
    matcher = FeatureMatcher(mock_resolver)
    f = Feature(name="t", prompt="p", source="m", hostname="h", page_type="p", target="t", target_type="s", action="a", selector="s", enabled=False)
    
    result = await matcher.match("h", "p", [f])
    assert len(result.matches) == 1
    m = result.matches[0]
    assert m.status == "disabled"
    assert m.confidence == 0.0
    mock_resolver.resolve.assert_not_called()

@pytest.mark.asyncio
async def test_matcher_no_base_match(mock_resolver):
    matcher = FeatureMatcher(mock_resolver)
    f = Feature(name="t", prompt="p", source="m", hostname="h", page_type="p", target="t", target_type="s", action="a", selector="s")
    
    result = await matcher.match("other", "other", [f])
    m = result.matches[0]
    assert m.status == "partial"
    assert m.confidence == 0.0
    assert "Hostname mismatch" in m.reason
    assert "Page type mismatch" in m.reason
    mock_resolver.resolve.assert_not_called()

@pytest.mark.asyncio
async def test_matcher_hostname_only(mock_resolver):
    matcher = FeatureMatcher(mock_resolver)
    f = Feature(name="t", prompt="p", source="m", hostname="h", page_type="p", target="t", target_type="s", action="a", selector="s")
    
    mock_resolver.resolve.return_value = ResolutionResult(matched=False, selector="", confidence=0, explanation="", candidate_count=0, top_candidates=[])
    
    result = await matcher.match("h", "other", [f])
    m = result.matches[0]
    assert m.status == "stale"
    assert m.confidence == 0.5
    assert m.feature_health == 0.0
    assert "Hostname matched" in m.reason
    assert "Page type mismatch" in m.reason
    mock_resolver.resolve.assert_called_once()

@pytest.mark.asyncio
async def test_matcher_full_match(mock_resolver):
    matcher = FeatureMatcher(mock_resolver)
    f = Feature(name="t", prompt="p", source="m", hostname="h", page_type="p", target="t", target_type="s", action="a", selector="s")
    
    mock_resolver.resolve.return_value = ResolutionResult(matched=True, selector="#found", confidence=0.9, explanation="", candidate_count=1, top_candidates=[])
    
    result = await matcher.match("h", "p", [f])
    m = result.matches[0]
    assert m.status == "ready"
    assert m.confidence == 1.0
    assert m.feature_health == 1.0
    assert "Target matched" in m.reason
