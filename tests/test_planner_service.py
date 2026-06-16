import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from promptdom.planning.service import PlannerService
from promptdom.planning.rule_planner import RulePlanner
from promptdom.planning.llm_planner import LLMPlanner
from promptdom.planning.models import PlannerResult

@pytest.fixture
def mock_inspection_service():
    service = MagicMock()
    service.inspect_compact = AsyncMock()
    # Also mock browser_manager for log extraction
    service.browser_manager = MagicMock()
    service.browser_manager.get_active_page = AsyncMock()
    return service

@pytest.mark.asyncio
async def test_planner_service_initialization(mock_inspection_service, monkeypatch):
    monkeypatch.setenv("PROMPTDOM_PLANNER", "RULE")
    service = PlannerService(mock_inspection_service)
    assert isinstance(service.planner, RulePlanner)
    
    monkeypatch.setenv("PROMPTDOM_PLANNER", "LLM")
    service = PlannerService(mock_inspection_service)
    assert isinstance(service.planner, LLMPlanner)

@pytest.mark.asyncio
async def test_planner_service_get_plan(mock_inspection_service, monkeypatch, tmp_path):
    monkeypatch.setenv("PROMPTDOM_PLANNER", "RULE")
    
    # Mock context
    from promptdom.inspection.models import CompactInspectionResponse
    mock_context = CompactInspectionResponse(
        title="Test",
        page_type="unknown",
        sections=[],
        visible_text_sample=""
    )
    mock_inspection_service.inspect_compact.return_value = mock_context
    
    # Mock browser manager page for logging
    mock_page = MagicMock()
    mock_page.url = "http://example.com"
    mock_inspection_service.browser_manager.get_active_page.return_value = mock_page
    
    service = PlannerService(mock_inspection_service)
    
    # Override log file to avoid creating local file during tests
    log_file = tmp_path / "test_planner_replay.jsonl"
    service.log_file = str(log_file)
    
    result = await service.get_plan("hide comments")
    
    assert isinstance(result, PlannerResult)
    assert len(result.plans) == 1
    assert result.plans[0].action == "hide"
    assert result.plans[0].target == "comments"
    
    # Verify logging
    assert os.path.exists(log_file)
    with open(log_file, "r") as f:
        log_content = f.read()
        assert "hide comments" in log_content
        assert "http://example.com" in log_content
        assert "example.com" in log_content
