import pytest
from unittest.mock import AsyncMock
from promptdom.transform.executor import TransformExecutor

@pytest.mark.asyncio
async def test_apply_css():
    mock_browser = AsyncMock()
    executor = TransformExecutor(mock_browser)
    
    success = await executor.apply_css("123", "body { display: none; }")
    assert success is True
    
    mock_browser.execute_js.assert_called_once()
    script = mock_browser.execute_js.call_args[0][0]
    
    assert "data-promptdom-id" in script
    assert "promptdom-transform-123" in script
    assert "body { display: none; }" in script

@pytest.mark.asyncio
async def test_apply_empty_css():
    mock_browser = AsyncMock()
    executor = TransformExecutor(mock_browser)
    
    success = await executor.apply_css("123", "  ")
    assert success is False
    mock_browser.execute_js.assert_not_called()

@pytest.mark.asyncio
async def test_apply_javascript():
    mock_browser = AsyncMock()
    executor = TransformExecutor(mock_browser)
    
    success = await executor.apply_javascript("123", "console.log('test');")
    assert success is True
    
    mock_browser.execute_js.assert_called_once()
    script = mock_browser.execute_js.call_args[0][0]
    
    assert "try {" in script
    assert "console.log('test');" in script
    assert "[PromptDOM Transform Error]" in script

@pytest.mark.asyncio
async def test_remove_transformation():
    mock_browser = AsyncMock()
    executor = TransformExecutor(mock_browser)
    
    success = await executor.remove_transformation("123")
    assert success is True
    
    mock_browser.execute_js.assert_called_once()
    script = mock_browser.execute_js.call_args[0][0]
    
    assert "promptdom-transform-123" in script
    assert "style.remove()" in script
