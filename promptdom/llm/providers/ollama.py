import time
import httpx
from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel
from ..base import BaseLLMProvider
from ..models import LLMResponse, ProviderCapabilities
from ..exceptions import ProviderConnectionError, ProviderTimeoutError, ProviderResponseError, ProviderValidationError

T = TypeVar('T', bound=BaseModel)

class OllamaProvider(BaseLLMProvider):
    def __init__(self, model_name: str, timeout: int = 30):
        self.base_url = "http://localhost:11434/api"
        self.model_name = model_name
        self.timeout = timeout
        
    @property
    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            supports_streaming=False,
            supports_json_mode=True,
            supports_tools=False,
            supports_vision=True, # Actually assuming ollama vision models are used if needed
            supports_system_prompt=True,
            max_image_count=1,
            max_image_size_mb=10.0
        )

    async def _post(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/{endpoint}",
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
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": 16384
            }
        }
        if system_prompt:
            payload["system"] = system_prompt
            
        data = await self._post("generate", payload)
        
        latency_ms = (time.time() - start_time) * 1000
        content = data.get("response", "")
        usage = {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0)
        }
        
        return LLMResponse(
            content=content,
            provider="OLLAMA",
            model=self.model_name,
            latency_ms=latency_ms,
            token_usage=usage,
            finish_reason="stop" if data.get("done") else "unknown"
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
            "prompt": prompt,
            "stream": False,
            "format": schema.model_json_schema(),
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": 16384
            }
        }
        if enhanced_system:
            payload["system"] = enhanced_system
            
        data = await self._post("generate", payload)
        content = data.get("response", "")
        
        import json
        try:
            parsed = json.loads(content)
            if "properties" in parsed and isinstance(parsed["properties"], dict):
                # If the LLM nested the response inside 'properties' due to seeing it in the schema prompt
                parsed = parsed["properties"]
            return schema.model_validate(parsed)
        except Exception as e:
            raise ProviderValidationError(f"Failed to parse provider output into schema: {str(e)}\nOutput: {content}")

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
        enhanced_system += f"\nRespond ONLY in valid JSON matching this schema: {schema_json}"
        
        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "images": images_base64,
            "stream": False,
            "format": schema.model_json_schema(),
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": 16384
            }
        }
        if enhanced_system:
            payload["system"] = enhanced_system
            
        data = await self._post("generate", payload)
        content = data.get("response", "")
        
        import json
        try:
            parsed = json.loads(content)
            if "properties" in parsed and isinstance(parsed["properties"], dict):
                parsed = parsed["properties"]
            return schema.model_validate(parsed)
        except Exception as e:
            raise ProviderValidationError(f"Failed to parse multimodal provider output into schema: {str(e)}\nOutput: {content}")
