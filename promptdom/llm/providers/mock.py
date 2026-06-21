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
            supports_system_prompt=True,
            max_image_count=0,
            max_image_size_mb=0.0
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> LLMResponse:
        content = None
        for item in self.dataset:
            if prompt.lower() in item["prompt"].lower() or item["prompt"].lower() in prompt.lower():
                content = json.dumps(item["expected"])
                break
                
        if content is None:
            raise ValueError("prompt_not_in_dataset")
                
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
        try:
            resp = await self.generate(prompt, system_prompt, temperature, max_tokens)
            return schema.model_validate_json(resp.content)
        except ValueError as e:
            if str(e) == "prompt_not_in_dataset" and schema.__name__ == "DesignPlan":
                mock_design = {
                    "goal": f"Generic Mock Redesign based on: '{prompt}'",
                    "layout_strategy": {
                        "primary_layout": "clean_minimalist",
                        "navigation_position": "left_sidebar",
                        "content_density": "spacious"
                    },
                    "content_strategy": {
                        "remove": ["Clutter", "Ads"],
                        "prioritize": ["Main Content"]
                    },
                    "visual_strategy": {
                        "theme": "sleek_dark",
                        "spacing": "generous",
                        "card_style": "elevated"
                    },
                    "changes": [
                        {"type": "REMOVE", "target": "Annoying Banner"},
                        {"type": "RESTYLE", "target": "Main Video", "style_goal": "Make it cinematic"}
                    ],
                    "confidence": 0.85,
                    "reasoning": "Since this is the Mock LLM provider, this is a placeholder redesign plan. Set PROMPTDOM_LLM_PROVIDER=OLLAMA in your .env file to use a real AI model."
                }
                return schema.model_validate(mock_design)
            raise e

    async def generate_multimodal_structured(
        self,
        prompt: str,
        images_base64: list[str],
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> T:
        raise NotImplementedError("Mock provider does not support multimodal")
