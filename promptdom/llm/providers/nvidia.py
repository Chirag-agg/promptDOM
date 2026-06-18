from typing import Optional
from .openai_compatible import BaseOpenAICompatibleProvider

class NvidiaNimProvider(BaseOpenAICompatibleProvider):
    def __init__(self, model_name: str, api_key: str, timeout: int = 30, base_url: Optional[str] = None):
        if not api_key:
            raise ValueError("Nvidia API key is required for Nvidia NIM provider.")
            
        if model_name.startswith("nvidia_nim/"):
            model_name = model_name[len("nvidia_nim/"):]
        
        # Depending on the specific Nvidia endpoint, the base URL is usually the completion endpoint minus /chat/completions
        # e.g., "https://integrate.api.nvidia.com/v1"
        super().__init__(
            base_url=base_url or "https://integrate.api.nvidia.com/v1",
            model_name=model_name,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}"
            }
        )

    # Note: If Nvidia supports vision, we can override generate_multimodal_structured here
    # but for now, we rely on the base class's NotImplementedError or we can implement it
    # if we know Nvidia's multimodal format. Nvidia NIM uses OpenAI's multimodal format.
    # We can override it here.
    
    async def generate_multimodal_structured(
        self,
        prompt: str,
        images_base64: list[str],
        schema: type,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ):
        import time
        from ..exceptions import ProviderValidationError
        
        start_time = time.time()
        
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
        
        payload = {
            "model": self.model_name,
            "messages": messages,
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

    @property
    def capabilities(self):
        from ..models import ProviderCapabilities
        return ProviderCapabilities(
            supports_streaming=False,
            supports_json_mode=True,
            supports_tools=False,
            supports_vision=True, # Assuming Nvidia vision models are used if needed
            supports_system_prompt=True,
            max_image_count=1,
            max_image_size_mb=10.0
        )
