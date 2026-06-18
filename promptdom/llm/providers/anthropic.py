import time
import httpx
from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel
from ..base import BaseLLMProvider
from ..models import LLMResponse, ProviderCapabilities
from ..exceptions import ProviderConnectionError, ProviderTimeoutError, ProviderResponseError, ProviderValidationError

T = TypeVar('T', bound=BaseModel)

class AnthropicProvider(BaseLLMProvider):
    def __init__(self, model_name: str, api_key: str, timeout: int = 30, base_url: Optional[str] = None):
        self.model_name = model_name
        self.api_key = api_key or "sk-dummy"
        self.timeout = timeout
        self.base_url = base_url or "https://api.anthropic.com"
        
    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=False,
            supports_json_mode=False, # Anthropic doesn't have native json_object response_format until recently, but we'll use prompt engineering
            supports_tools=False,
            supports_vision=True,
            supports_system_prompt=True,
            max_image_count=5,
            max_image_size_mb=5.0
        )

    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                headers = {
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                response = await client.post(
                    f"{self.base_url}/v1/messages",
                    json=payload,
                    headers=headers
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
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            payload["system"] = system_prompt
            
        data = await self._post(payload)
        
        latency_ms = (time.time() - start_time) * 1000
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
                
        usage = data.get("usage", {})
        
        return LLMResponse(
            content=content,
            provider="ANTHROPIC",
            model=self.model_name,
            latency_ms=latency_ms,
            token_usage=usage,
            finish_reason=data.get("stop_reason")
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> T:
        schema_json = schema.model_json_schema()
        enhanced_system = system_prompt or "You are a helpful assistant."
        enhanced_system += f"\nRespond ONLY in valid JSON matching this schema: {schema_json}. Do not include markdown formatting or extra text."
        
        resp = await self.generate(prompt, enhanced_system, temperature, max_tokens)
        
        # strip markdown if present
        content = resp.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
            
        try:
            return schema.model_validate_json(content.strip())
        except Exception as e:
            raise ProviderValidationError(f"Failed to parse output: {str(e)}\nOutput: {content}")

    async def generate_multimodal_structured(
        self,
        prompt: str,
        images_base64: list[str],
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> T:
        start_time = time.time()
        
        schema_json = schema.model_json_schema()
        enhanced_system = system_prompt or "You are a helpful assistant."
        enhanced_system += f"\nRespond ONLY in valid JSON matching this schema: {schema_json}. Do not include markdown formatting or extra text."
        
        content_items = []
        for b64 in images_base64:
            content_items.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": b64
                }
            })
        content_items.append({"type": "text", "text": prompt})
        
        payload = {
            "model": self.model_name,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": content_items}]
        }
        if enhanced_system:
            payload["system"] = enhanced_system
            
        data = await self._post(payload)
        
        content = ""
        for block in data.get("content", []):
            if block.get("type") == "text":
                content += block.get("text", "")
                
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
            
        try:
            return schema.model_validate_json(content.strip())
        except Exception as e:
            raise ProviderValidationError(f"Failed to parse output: {str(e)}\nOutput: {content}")
