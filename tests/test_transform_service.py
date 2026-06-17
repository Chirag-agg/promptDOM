import pytest
from unittest.mock import AsyncMock, MagicMock
from promptdom.transform.service import ExperimentalTransformationService
from promptdom.transform.models import GeneratedTransformation
from promptdom.inspection.models import InspectionResponse, PageSection, PageButton, DOMSummary

@pytest.fixture
def mock_inspection_service():
    service = AsyncMock()
    service.inspect.return_value = InspectionResponse(
        url="https://youtube.com", 
        title="YouTube",
        hostname="youtube.com",
        page_type="video_platform",
        dom_fingerprint="123",
        headings=[],
        sections=[PageSection(role="region", identifier="shorts", tag="div", id="shorts", classes="shorts-container")],
        buttons=[PageButton(text="Subscribe", tag="button", id="sub", classes="")],
        inputs=[],
        links=[],
        interactive_elements=[],
        visible_text_sample="Some visible text",
        summary=DOMSummary(heading_count=0, button_count=1, input_count=0, link_count=0, section_count=1, visible_text_length=10)
    )
    return service

@pytest.fixture
def mock_provider():
    provider = AsyncMock()
    provider.generate_structured.return_value = GeneratedTransformation(
        css=".shorts-container { display: none; }",
        javascript="console.log('Hidden shorts');",
        reasoning="User wanted to hide shorts.",
        confidence=0.9,
        affected_elements=["#shorts"],
        transformation_type="hide"
    )
    provider.generate_text.return_value = "- Will hide: Shorts"
    return provider

@pytest.mark.asyncio
async def test_generate_transformation(mock_provider, mock_inspection_service):
    service = ExperimentalTransformationService(mock_provider, mock_inspection_service)
    
    result = await service.generate_transformation("hide shorts")
    
    assert result.css == ".shorts-container { display: none; }"
    assert result.confidence == 0.9
    
    mock_inspection_service.inspect.assert_called_once()
    mock_provider.generate_structured.assert_called_once()
    
    # Verify prompt contains inspection data
    call_args = mock_provider.generate_structured.call_args[1]
    assert "https://youtube.com" in call_args["prompt"]
    assert "shorts-container" in call_args["prompt"]

@pytest.mark.asyncio
async def test_generate_preview(mock_provider, mock_inspection_service):
    service = ExperimentalTransformationService(mock_provider, mock_inspection_service)
    
    preview = await service.generate_preview("hide shorts")
    
    assert preview.ui_diff_summary == "- Will hide: Shorts"
    assert preview.transformation.css == ".shorts-container { display: none; }"
    assert preview.transformation_id is not None
    
    assert service.get_preview(preview.transformation_id) == preview
