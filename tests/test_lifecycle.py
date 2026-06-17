import pytest
from unittest.mock import AsyncMock, MagicMock
from promptdom.runtime.lifecycle import LifecycleManager
from promptdom.runtime.registry import RuntimeRegistry
from promptdom.compiler.models import CompiledFeature, HideElementAction, FeatureSpec
from promptdom.compiler.ast import FeatureAST, ActionAST
from promptdom.analytics.collector import AnalyticsCollector

@pytest.fixture
def lifecycle():
    registry = RuntimeRegistry()
    browser = AsyncMock()
    analytics = MagicMock()
    return LifecycleManager(registry, browser, analytics)

@pytest.mark.asyncio
async def test_lifecycle_install(lifecycle):
    spec = FeatureSpec(name="test", actions=[HideElementAction(selector="test")])
    ast = FeatureAST(name="test", actions=[ActionAST(action_id="123", action_type="hide_element", selector="test")])
    compiled = CompiledFeature(
        javascript="console.log('hi');",
        source_spec=spec,
        ast=ast
    )
    
    instance = await lifecycle.install_and_run(compiled, "feat1")
    
    assert instance.feature_id == "feat1"
    assert instance.state.value == "RUNNING"
    
    lifecycle.browser.execute_js.assert_called_once()
    executed_js = lifecycle.browser.execute_js.call_args[0][0]
    
    # Assert wrapper mechanics
    assert "window.__promptdom.features" in executed_js
    assert "setInterval" in executed_js
    assert "console.log('hi');" in executed_js
