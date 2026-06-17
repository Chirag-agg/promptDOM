import pytest
import os
from pydantic import BaseModel
from promptdom.config.llm import LLMSettings
from promptdom.llm.provider_factory import ProviderFactory
from promptdom.llm.providers.mock import MockProvider
from promptdom.llm.providers.ollama import OllamaProvider

class DummySchema(BaseModel):
    action: str
    target: str

def test_factory_resolves_mock():
    config = LLMSettings(provider="MOCK")
    provider = ProviderFactory.get_provider(config)
    assert isinstance(provider, MockProvider)

def test_factory_resolves_ollama():
    config = LLMSettings(provider="OLLAMA")
    provider = ProviderFactory.get_provider(config)
    assert isinstance(provider, OllamaProvider)

def test_factory_unknown_provider():
    config = LLMSettings(provider="UNKNOWN")
    with pytest.raises(ValueError, match="Unknown LLM Provider"):
        ProviderFactory.get_provider(config)

@pytest.mark.asyncio
async def test_mock_provider_generate():
    provider = MockProvider()
    resp = await provider.generate(prompt="hide comments")
    
    assert resp.provider == "MOCK"
    assert resp.model == "mock-v1"
    assert "comments" in resp.content
    assert resp.finish_reason == "stop"

@pytest.mark.asyncio
async def test_mock_provider_structured():
    provider = MockProvider()
    # "hide comments" matches dataset which returns {"action": "hide", "target": "comments", "target_type": "section"}
    resp = await provider.generate_structured(prompt="hide comments", schema=DummySchema)
    
    assert resp.action == "hide"
    assert resp.target == "comments"

def test_ollama_not_implemented():
    provider = OllamaProvider()
    with pytest.raises(NotImplementedError):
        _ = provider.capabilities
