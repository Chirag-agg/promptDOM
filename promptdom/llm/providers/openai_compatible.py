import time
import httpx
from typing import Optional, Type, TypeVar, Dict, Any
from pydantic import BaseModel
from ..base import BaseLLMProvider
from ..models import LLMResponse, ProviderCapabilities
from ..exceptions import ProviderConnectionError, ProviderTimeoutError, ProviderResponseError, ProviderValidationError

T = TypeVar('T', bound=BaseModel)

class BaseOpenAICompatibleProvider(BaseLLMProvider):
    def __init__(self, base_url: str, model_name: str, timeout: int = 30, headers: Optional[Dict[str, str]] = None):
        self.base_url = base_url
        self.model_name = model_name
        self.timeout = timeout
        self.headers = headers
        
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

    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        import json
        payload["stream"] = True
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                kwargs = {"json": payload}
                if self.headers:
                    kwargs["headers"] = self.headers
                
                full_content = ""
                finish_reason = None
                usage = {}
                
                async with client.stream("POST", f"{self.base_url}/chat/completions", **kwargs) as response:
                    if response.status_code != 200:
                        await response.aread()
                        raise ProviderResponseError(f"HTTP {response.status_code}: {response.text}")
                        
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line or line == "data: [DONE]":
                            continue
                        if line.startswith("data: "):
                            data_str = line[6:]
                            try:
                                chunk = json.loads(data_str)
                                choices = chunk.get("choices", [])
                                if choices:
                                    delta = choices[0].get("delta", {})
                                    if "content" in delta and delta["content"]:
                                        full_content += delta["content"]
                                    if "finish_reason" in choices[0] and choices[0]["finish_reason"]:
                                        finish_reason = choices[0]["finish_reason"]
                                if "usage" in chunk and chunk["usage"]:
                                    usage = chunk["usage"]
                            except json.JSONDecodeError:
                                pass
                                
                return {
                    "choices": [{
                        "message": {
                            "content": full_content
                        },
                        "finish_reason": finish_reason or "stop"
                    }],
                    "usage": usage
                }
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
        enhanced_system += f"\nRespond ONLY with a valid JSON instance containing the actual data. Do not repeat the schema itself. The JSON object must strictly conform to the following schema:\n{schema_json}"
        
        payload = {
            "model": self.model_name,
            "messages": self._build_messages(prompt + "\n\nIMPORTANT: You MUST output the actual populated JSON data instance. Do NOT output the schema definitions. Just the final JSON object.", enhanced_system),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }
        
        data = await self._post(payload)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        try:
            import json
            parsed = json.loads(content)
            
            def _extract_schema_values(data):
                if isinstance(data, dict):
                    if "type" in data and ("value" in data or "default" in data):
                        return data.get("value", data.get("default"))
                    if "properties" in data and isinstance(data["properties"], dict):
                        return _extract_schema_values(data["properties"])
                    new_data = {}
                    for k, v in data.items():
                        new_data[k] = _extract_schema_values(v)
                    return new_data
                elif isinstance(data, list):
                    return [_extract_schema_values(item) for item in data]
                return data

            parsed = _extract_schema_values(parsed)
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
        raise NotImplementedError("OpenAI compatible providers do not yet support multimodal generation in this client")
