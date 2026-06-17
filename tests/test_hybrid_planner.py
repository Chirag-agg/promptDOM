import pytest
from promptdom.planning.models import ActionPlan, PlannerResult, PlannerContext
from promptdom.planning.hybrid_planner import HybridPlannerService
from promptdom.inspection.models import CompactInspectionResponse
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_rule_planner():
    planner = MagicMock()
    planner.inspection_service = MagicMock()
    planner.inspection_service.inspect_compact = AsyncMock(return_value=CompactInspectionResponse(
        title="Mock", page_type="mock", visible_text_sample="", sections=[]
    ))
    return planner

@pytest.fixture
def mock_llm_planner():
    planner = MagicMock()
    return planner

@pytest.fixture
def mock_analytics():
    return MagicMock()

@pytest.mark.asyncio
async def test_hybrid_planner_uses_rule_when_confident(mock_rule_planner, mock_llm_planner, mock_analytics):
    hybrid = HybridPlannerService(mock_rule_planner, mock_llm_planner, mock_analytics)
    
    mock_rule_planner.get_plan = AsyncMock(return_value=PlannerResult(
        plans=[ActionPlan(action="hide", target="comments", target_type="section", confidence=0.85, reasoning="")]
    ))
    
    result = await hybrid.get_plan("hide comments")
    
    assert result.plans[0].planner_source == "HYBRID_RULE"
    mock_llm_planner.plan.assert_not_called()

@pytest.mark.asyncio
async def test_hybrid_planner_falls_back_to_llm(mock_rule_planner, mock_llm_planner, mock_analytics):
    hybrid = HybridPlannerService(mock_rule_planner, mock_llm_planner, mock_analytics)
    
    mock_rule_planner.get_plan = AsyncMock(return_value=PlannerResult(
        plans=[ActionPlan(action="hide", target="comments", target_type="section", confidence=0.5, reasoning="")]
    ))
    
    mock_llm_planner.plan = AsyncMock(return_value=ActionPlan(
        action="hide", target="comments", target_type="section", confidence=0.9, reasoning=""
    ))
    
    result = await hybrid.get_plan("hide comments")
    
    assert result.plans[0].planner_source == "HYBRID_LLM"
    assert result.plans[0].fallback_reason == "low_confidence"

@pytest.mark.asyncio
async def test_hybrid_planner_handles_llm_failure(mock_rule_planner, mock_llm_planner, mock_analytics):
    hybrid = HybridPlannerService(mock_rule_planner, mock_llm_planner, mock_analytics)
    
    mock_rule_planner.get_plan = AsyncMock(return_value=PlannerResult(
        plans=[ActionPlan(action="hide", target="comments", target_type="section", confidence=0.5, reasoning="")]
    ))
    
    mock_llm_planner.plan = AsyncMock(side_effect=Exception("Provider offline"))
    
    result = await hybrid.get_plan("hide comments")
    
    assert result.plans[0].planner_source == "HYBRID_RULE"
    assert result.plans[0].fallback_reason == "provider_failure"
