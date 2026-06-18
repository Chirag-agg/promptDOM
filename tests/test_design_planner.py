import pytest
from unittest.mock import AsyncMock, MagicMock
from promptdom.design.service import DesignPlanner
from promptdom.design.models import DesignPlan, LayoutStrategy, ContentStrategy, VisualStrategy
from promptdom.inspection.models import CompactInspectionResponse
from promptdom.visual.models import VisualInspectionResponse, VisualContext

@pytest.mark.asyncio
async def test_design_planner_flow():
    mock_provider = AsyncMock()
    
    # Setup mock responses
    initial_plan = DesignPlan(
        goal="Test Goal",
        layout_strategy=LayoutStrategy(
            primary_layout="feed",
            navigation_position="left",
            content_density="high"
        ),
        content_strategy=ContentStrategy(
            remove=["Ads"],
            prioritize=["Content"]
        ),
        visual_strategy=VisualStrategy(
            theme="dark",
            spacing="compact",
            card_style="flat"
        ),
        confidence=0.8,
        reasoning="Initial thought"
    )
    
    improved_plan = DesignPlan(
        goal="Test Goal",
        layout_strategy=LayoutStrategy(
            primary_layout="feed",
            navigation_position="left",
            content_density="high"
        ),
        content_strategy=ContentStrategy(
            remove=["Ads", "Sidebar"],
            prioritize=["Content"]
        ),
        visual_strategy=VisualStrategy(
            theme="dark",
            spacing="compact",
            card_style="flat"
        ),
        confidence=0.9,
        reasoning="Critiqued thought"
    )
    
    # Mock sequence: first returns initial, second returns improved
    mock_provider.generate_structured.side_effect = [initial_plan, improved_plan]
    
    planner = DesignPlanner(mock_provider)
    planner.provider.capabilities = MagicMock()
    planner.provider.capabilities.supports_vision = False

    compact_inspection = CompactInspectionResponse(
        url="https://test.com",
        title="Test",
        page_type="unknown",
        sections=[],
        buttons=[],
        links=[],
        visible_text_sample="Hello"
    )
    
    visual_context = VisualContext(
        screenshot_id="test",
        screenshot_path="test.png",
        page_url="https://test.com",
        width=1920,
        height=1080,
        created_at="now"
    )
    
    inspection = VisualInspectionResponse(
        page_context=compact_inspection,
        visual_context=visual_context
    )

    final_plan = await planner.generate_plan("Redesign this", inspection)
    
    assert final_plan.confidence == 0.9
    assert "Sidebar" in final_plan.content_strategy.remove
    assert mock_provider.generate_structured.call_count == 2
