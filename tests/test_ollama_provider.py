import pytest
from unittest.mock import patch, AsyncMock
from promptdom.llm.providers.ollama import OllamaProvider
from promptdom.llm.exceptions import ProviderConnectionError
import httpx

@pytest.fixture
def provider():
    return OllamaProvider(model_name="test-model", timeout=5)

@pytest.mark.asyncio
async def test_ollama_generate_success(provider):
    mock_response = AsyncMock()
    mock_response.status_code = 200
    mock_response.json = lambda: {
        "response": "Here is a plan",
        "prompt_eval_count": 10,
        "eval_count": 5,
        "done": True
    }
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        resp = await provider.generate("hide comments")
        
        assert resp.content == "Here is a plan"
        assert resp.model == "test-model"
        assert resp.token_usage["prompt_tokens"] == 10
        assert resp.token_usage["completion_tokens"] == 5

@pytest.mark.asyncio
async def test_ollama_connection_error(provider):
    with patch("httpx.AsyncClient.post", side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(ProviderConnectionError):
            await provider.generate("hide comments")
