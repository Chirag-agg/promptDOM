import pytest
from unittest.mock import patch, AsyncMock
from promptdom.llm.providers.lmstudio import LMStudioProvider
from promptdom.llm.exceptions import ProviderConnectionError
import httpx

@pytest.fixture
def provider():
    return LMStudioProvider(model_name="test-model", timeout=5)

@pytest.mark.asyncio
async def test_lmstudio_generate_success(provider):
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        "choices": [{"message": {"content": "Here is a plan"}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
    }
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        resp = await provider.generate("hide comments")
        
        assert resp.content == "Here is a plan"
        assert resp.model == "test-model"
        assert resp.token_usage["prompt_tokens"] == 10
        assert resp.token_usage["completion_tokens"] == 5

@pytest.mark.asyncio
async def test_lmstudio_connection_error(provider):
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(ProviderConnectionError):
            await provider.generate("hide comments")
