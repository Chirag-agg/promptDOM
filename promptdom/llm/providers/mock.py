import json
import os
import time
from typing import Optional, Type, TypeVar
from pydantic import BaseModel
from ..base import BaseLLMProvider
from ..models import LLMResponse, ProviderCapabilities

T = TypeVar('T', bound=BaseModel)

class MockProvider(BaseLLMProvider):
    def __init__(self):
        self.dataset_path = os.path.join("datasets", "planning.json")
        self._dataset = None
    
    @property
    def dataset(self):
        if self._dataset is None:
            if os.path.exists(self.dataset_path):
                with open(self.dataset_path, "r", encoding="utf-8") as f:
                    self._dataset = json.load(f)
            else:
                self._dataset = []
        return self._dataset

    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=False,
            supports_json_mode=True,
            supports_tools=False,
            supports_vision=False,
            supports_system_prompt=True
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> LLMResponse:
        content = "{}"
        for item in self.dataset:
            if item["prompt"].lower() in prompt.lower():
                content = json.dumps(item["expected"])
                break
                
        return LLMResponse(
            content=content,
            provider="MOCK",
            model="mock-v1",
            latency_ms=12.5,
            token_usage={"prompt_tokens": 10, "completion_tokens": 20},
            finish_reason="stop"
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> T:
        resp = await self.generate(prompt, system_prompt, temperature, max_tokens)
        return schema.model_validate_json(resp.content)
