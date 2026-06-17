import time
import httpx
from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel
from ..base import BaseLLMProvider
from ..models import LLMResponse, ProviderCapabilities
from ..exceptions import ProviderConnectionError, ProviderTimeoutError, ProviderResponseError, ProviderValidationError

T = TypeVar('T', bound=BaseModel)

class BaseOpenAICompatibleProvider(BaseLLMProvider):
    def __init__(self, base_url: str, model_name: str, timeout: int = 30):
        self.base_url = base_url
        self.model_name = model_name
        self.timeout = timeout
        
    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=False,
            supports_json_mode=True,
            supports_tools=False,
            supports_vision=False,
            supports_system_prompt=True
        )

    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    json=payload
                )
                if response.status_code != 200:
                    raise ProviderResponseError(f"HTTP {response.status_code}: {response.text}")
                return response.json()
        except httpx.ConnectError as e:
            raise ProviderConnectionError(f"Connection failed: {str(e)}")
        except httpx.TimeoutException as e:
            raise ProviderTimeoutError(f"Request timed out after {self.timeout}s: {str(e)}")
        except httpx.RequestError as e:
            raise ProviderConnectionError(f"Request failed: {str(e)}")

    def _build_messages(self, prompt: str, system_prompt: Optional[str]) -> list:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        return messages

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> LLMResponse:
        start_time = time.time()
        
        payload = {
            "model": self.model_name,
            "messages": self._build_messages(prompt, system_prompt),
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        data = await self._post(payload)
        
        latency_ms = (time.time() - start_time) * 1000
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=content,
            provider=self.__class__.__name__.replace("Provider", "").upper(),
            model=self.model_name,
            latency_ms=latency_ms,
            token_usage=usage,
            finish_reason=data.get("choices", [{}])[0].get("finish_reason")
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> T:
        start_time = time.time()
        
        # Inject JSON instruction
        schema_json = schema.model_json_schema()
        enhanced_system = system_prompt or "You are a helpful assistant."
        enhanced_system += f"\nRespond ONLY in valid JSON matching this schema: {schema_json}"
        
        payload = {
            "model": self.model_name,
            "messages": self._build_messages(prompt, enhanced_system),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }
        
        data = await self._post(payload)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        try:
            return schema.model_validate_json(content)
        except Exception as e:
            raise ProviderValidationError(f"Failed to parse provider output into schema: {str(e)}\nOutput: {content}")
