import pytest
import json
import os
from promptdom.planning.rule_planner import RulePlanner
from promptdom.planning.models import PlannerContext
from promptdom.inspection.models import CompactInspectionResponse, PageSection

@pytest.fixture
def mock_context():
    page_context = CompactInspectionResponse(
        title="Test Page",
        page_type="article",
        sections=[
            PageSection(role="main", identifier="content", text_preview="Article"),
            PageSection(role="aside", identifier="sidebar", text_preview="Sidebar links"),
            PageSection(role="section", identifier="comments-area", text_preview="User comments")
        ],
        visible_text_sample="Article and Sidebar links and User comments"
    )
    return page_context

@pytest.mark.asyncio
async def test_rule_planner_against_benchmark(mock_context):
    planner = RulePlanner()
    cases_path = os.path.join(os.path.dirname(__file__), 'data', 'planner_cases.json')
    with open(cases_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
        
    for case in cases:
        context = PlannerContext(prompt=case["prompt"], page_context=mock_context)
        result = await planner.plan(context)
        
        # Verify action
        if result.plans:
            assert result.plans[0].action == case["expected_action"]
        
        # Verify targets
        targets = [p.target for p in result.plans]
        assert set(targets) == set(case["expected_targets"])
        
        # Verify confidence scores
        for plan in result.plans:
            if plan.target == "unknown":
                assert plan.confidence == 0.2
            elif plan.target in ["sidebar", "comments"]:
                assert plan.confidence == 0.95
                assert plan.target_type == "section"
