import pytest
from unittest.mock import AsyncMock, MagicMock
from promptdom.resolution.resolver import SemanticResolver
from promptdom.inspection.models import ResolutionInspectionResponse, PageSection

@pytest.fixture
def mock_inspection_service():
    service = MagicMock()
    service.inspect_resolution = AsyncMock()
    return service

@pytest.mark.asyncio
async def test_resolver_registry_fast_path(mock_inspection_service):
    inspection = ResolutionInspectionResponse(
        dom_fingerprint="test1234",
        headings=[], buttons=[], inputs=[], links=[], sections=[], interactive_elements=[]
    )
    mock_inspection_service.inspect_resolution.return_value = inspection
    
    resolver = SemanticResolver(mock_inspection_service)
    result = await resolver.resolve("youtube_shorts", "section")
    
    assert result.matched is True
    assert result.selector == "#shorts-container"
    assert "legacy" in result.explanation.lower()

@pytest.mark.asyncio
async def test_resolver_semantic_match(mock_inspection_service):
    inspection = ResolutionInspectionResponse(
        dom_fingerprint="test1234",
        headings=[], buttons=[], inputs=[], links=[],
        sections=[
            PageSection(role="section", identifier="rec", text_preview="recommended videos", id="recs-id", classes="", aria_label="", data_testid="", tag="section", css_path="")
        ],
        interactive_elements=[]
    )
    mock_inspection_service.inspect_resolution.return_value = inspection
    
    resolver = SemanticResolver(mock_inspection_service)
    
    # We clear registry to ensure it uses semantic match
    resolver.registry = {}
    
    result = await resolver.resolve("recommendations", "section")
    
    assert result.matched is True
    assert result.selector == "#recs-id"
    assert result.confidence >= 0.5
    assert "Synonym Match" in result.explanation

@pytest.mark.asyncio
async def test_resolver_ambiguous_failure(mock_inspection_service):
    inspection = ResolutionInspectionResponse(
        dom_fingerprint="test1234",
        headings=[], buttons=[], inputs=[], links=[],
        sections=[
            PageSection(role="section", identifier="unrelated", text_preview="totally unrelated", id="unrelated", classes="", aria_label="", data_testid="", tag="section", css_path="")
        ],
        interactive_elements=[]
    )
    mock_inspection_service.inspect_resolution.return_value = inspection
    
    resolver = SemanticResolver(mock_inspection_service)
    resolver.registry = {}
    
    result = await resolver.resolve("that thing", "section")
    
    assert result.matched is False
    assert result.confidence < 0.6
