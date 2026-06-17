import pytest
from unittest.mock import AsyncMock
from promptdom.llm.health import LLMHealthService
from promptdom.llm.providers.mock import MockProvider

@pytest.mark.asyncio
async def test_llm_health_success():
    provider = MockProvider()
    provider.generate = AsyncMock()
    
    service = LLMHealthService(provider, "mock-model", "MOCK")
    health = await service.check_provider()
    
    assert health.provider == "MOCK"
    assert health.reachable is True
    assert health.model == "mock-model"

@pytest.mark.asyncio
async def test_llm_health_failure():
    provider = MockProvider()
    provider.generate = AsyncMock(side_effect=Exception("Offline"))
    
    service = LLMHealthService(provider, "mock-model", "MOCK")
    health = await service.check_provider()
    
    assert health.reachable is False
