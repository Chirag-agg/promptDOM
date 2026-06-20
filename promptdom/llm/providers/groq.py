from typing import Optional
from .openai_compatible import BaseOpenAICompatibleProvider

class GroqProvider(BaseOpenAICompatibleProvider):
    def __init__(self, model_name: str, api_key: str, timeout: int = 60, base_url: Optional[str] = None):
        if not api_key:
            raise ValueError("Groq API key is required for Groq provider.")
            
        super().__init__(
            base_url=base_url or "https://api.groq.com/openai/v1",
            model_name=model_name,
            timeout=timeout,
            headers={
                "Authorization": f"Bearer {api_key}"
            }
        )

    # Groq supports vision for llama-3.2-90b-vision-preview and llama-3.2-11b-vision-preview
    # We can implement generate_multimodal_structured here just like OpenAI format
    async def generate_multimodal_structured(
        self,
        prompt: str,
        images_base64: list[str],
        schema: type,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
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
            import json
            parsed = json.loads(content)
            if "properties" in parsed and isinstance(parsed["properties"], dict) and len(parsed) == 1:
                parsed = parsed["properties"]
            return schema.model_validate(parsed)
        except Exception as e:
            raise ProviderValidationError(f"Failed to parse provider output into schema: {str(e)}\nOutput: {content}")

    @property
    def capabilities(self):
        from ..models import ProviderCapabilities
        return ProviderCapabilities(
            supports_streaming=True, # Groq streams incredibly fast
            supports_json_mode=True,
            supports_tools=False,
            supports_vision=True, 
            supports_system_prompt=True,
            max_image_count=1,
            max_image_size_mb=4.0
        )
