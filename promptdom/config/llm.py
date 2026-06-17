import os
from pydantic import BaseModel
from typing import Optional

class LLMSettings(BaseModel):
    provider: str = "MOCK"
    model: str = "mock-1"
    temperature: float = 0.0
    timeout_seconds: int = 30
    
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

def get_llm_settings() -> LLMSettings:
    return LLMSettings(
        provider=os.getenv("PROMPTDOM_LLM_PROVIDER", "MOCK").upper(),
        model=os.getenv("PROMPTDOM_LLM_MODEL", "mock-1"),
        timeout_seconds=int(os.getenv("PROMPTDOM_LLM_TIMEOUT", "30")),
        openai_api_key=os.getenv("PROMPTDOM_LLM_OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("PROMPTDOM_LLM_ANTHROPIC_API_KEY"),
    )
