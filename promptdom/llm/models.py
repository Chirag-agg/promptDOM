from pydantic import BaseModel
from typing import Optional

class ProviderCapabilities(BaseModel):
    supports_streaming: bool
    supports_json_mode: bool
    supports_tools: bool
    supports_vision: bool
    supports_system_prompt: bool

class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    latency_ms: float
    token_usage: Optional[dict] = None
    finish_reason: Optional[str] = None
