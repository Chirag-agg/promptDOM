from typing import Optional
from .openai_compatible import BaseOpenAICompatibleProvider

class GeminiProvider(BaseOpenAICompatibleProvider):
    def __init__(self, model_name: str, api_key: str, timeout: int = 120, base_url: Optional[str] = None):
        if not api_key:
            raise ValueError("Gemini API key is required for Gemini provider.")
            
        super().__init__(
            base_url=base_url or "https://generativelanguage.googleapis.com/v1beta/openai",
            model_name=model_name,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}"
            }
        )

    async def generate_multimodal_structured(
        self,
        prompt: str,
        images_base64: list[str],
        schema: type,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 8000
    ):
        from ..exceptions import ProviderValidationError
        
        schema_json = schema.model_json_schema()
        enhanced_system = system_prompt or "You are a helpful assistant."
        enhanced_system += f"\nRespond ONLY with a valid JSON instance containing the actual data. Do not repeat the schema itself. The JSON object must strictly conform to the following schema:\n{schema_json}"
        
        messages = []
        if enhanced_system:
            messages.append({"role": "system", "content": enhanced_system})
            
        content_items = [{"type": "text", "text": prompt}]
        for b64 in images_base64:
            content_items.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{b64}"
                }
            })
        content_items.append({"type": "text", "text": "IMPORTANT: You MUST output the actual populated JSON data instance. Do NOT output the schema definitions. Just the final JSON object."})
            
        messages.append({"role": "user", "content": content_items})
        
        if temperature < 0.5:
            temperature = 0.5

        payload = {
            "model": self.model_name,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "response_format": {"type": "json_object"}
        }
        
        data = await self._post(payload)
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        
        # Clean markdown code blocks if present
        import re
        import json
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'```$', '', content.strip()).strip()
        
        # Sometimes Gemini appends extra trailing characters like `}\n}`
        # We find the first `{` and then try parsing substrings ending at each `}` from the back
        start_idx = content.find('{')
        if start_idx != -1:
            content = content[start_idx:]
            while content:
                try:
                    json.loads(content)
                    break # Found valid JSON
                except json.JSONDecodeError:
                    end_idx = content.rfind('}')
                    if end_idx == -1:
                        break
                    content = content[:end_idx].strip()
        
        try:
            return schema.model_validate_json(content)
        except Exception as e:
            raise ProviderValidationError(f"Failed to parse provider output into schema: {str(e)}\nOutput: {content}")

    async def _post(self, payload: dict) -> dict:
        import httpx
        from ..exceptions import ProviderConnectionError, ProviderTimeoutError, ProviderResponseError
        
        payload["stream"] = False
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                kwargs = {"json": payload}
                if self.headers:
                    kwargs["headers"] = self.headers
                
                response = await client.post(f"{self.base_url}/chat/completions", **kwargs)
                if response.status_code != 200:
                    raise ProviderResponseError(f"HTTP {response.status_code}: {response.text}")
                    
                return response.json()
        except httpx.ConnectError as e:
            raise ProviderConnectionError(f"Connection failed: {str(e)}")
        except httpx.TimeoutException as e:
            raise ProviderTimeoutError(f"Request timed out after {self.timeout}s: {str(e)}")
        except httpx.RequestError as e:
            raise ProviderConnectionError(f"Request failed: {str(e)}")

    @property
    def capabilities(self):
        from ..models import ProviderCapabilities
        return ProviderCapabilities(
            supports_streaming=False,
            supports_json_mode=True,
            supports_tools=False,
            supports_vision=True, 
            supports_system_prompt=True,
            max_image_count=5,
            max_image_size_mb=4.0
        )

    async def generate_structured(
        self,
        prompt: str,
        schema: type,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 8192
    ):
        if temperature < 0.5:
            temperature = 0.5
            
        return await super().generate_structured(
            prompt=prompt,
            schema=schema,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 8192
    ):
        if temperature < 0.5:
            temperature = 0.5
            
        return await super().generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
