import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from promptdom.inspection.service import InspectionService
from promptdom.inspection.exceptions import NoActivePageError

@pytest.fixture
def mock_browser_manager():
    manager = MagicMock()
    manager.get_active_page = AsyncMock()
    return manager

@pytest.fixture
def mock_extractor():
    with patch("promptdom.inspection.service.DOMExtractor") as mock:
        yield mock.return_value

@pytest.mark.asyncio
async def test_service_inspect(mock_browser_manager, mock_extractor):
    # Setup mocks
    mock_page = MagicMock()
    mock_browser_manager.get_active_page.return_value = mock_page
    
    mock_extractor.extract = AsyncMock(return_value={
        "url": "http://test.com",
        "hostname": "test.com",
        "title": "Test",
        "page_type": "unknown",
        "dom_fingerprint": "hash123",
        "headings": [],
        "buttons": [],
        "inputs": [],
        "links": [],
        "sections": [],
        "interactive_elements": [],
        "visible_text_sample": "sample",
        "summary": {
            "heading_count": 0, "button_count": 0, "input_count": 0,
            "link_count": 0, "section_count": 0, "visible_text_length": 6
        }
    })
    
    service = InspectionService(mock_browser_manager)
    service.extractor = mock_extractor
    
    response = await service.inspect()
    
    assert response.url == "http://test.com"
    assert response.title == "Test"
    assert response.dom_fingerprint == "hash123"
    mock_extractor.extract.assert_called_once_with(mock_page)

@pytest.mark.asyncio
async def test_service_inspect_compact(mock_browser_manager, mock_extractor):
    mock_page = MagicMock()
    mock_browser_manager.get_active_page.return_value = mock_page
    
    mock_extractor.extract = AsyncMock(return_value={
        "url": "http://test.com",
        "hostname": "test.com",
        "title": "Compact Test",
        "page_type": "article",
        "dom_fingerprint": "hash123",
        "headings": [],
        "buttons": [],
        "inputs": [],
        "links": [],
        "sections": [{"role": "main", "identifier": "content", "text_preview": "test"}],
        "interactive_elements": [],
        "visible_text_sample": "sample",
        "summary": {
            "heading_count": 0, "button_count": 0, "input_count": 0,
            "link_count": 0, "section_count": 1, "visible_text_length": 6
        }
    })
    
    service = InspectionService(mock_browser_manager)
    service.extractor = mock_extractor
    
    response = await service.inspect_compact()
    
    assert response.title == "Compact Test"
    assert response.page_type == "article"
    assert len(response.sections) == 1

@pytest.mark.asyncio
async def test_service_handles_exceptions(mock_browser_manager):
    # Simulate NoActivePageError from get_active_page
    mock_browser_manager.get_active_page.side_effect = NoActivePageError("No active pages found.")
    
    service = InspectionService(mock_browser_manager)
    
    with pytest.raises(NoActivePageError):
        await service.inspect()
