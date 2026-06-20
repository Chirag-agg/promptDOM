import os
from pydantic import BaseModel
from typing import Optional

class LLMSettings(BaseModel):
    provider: str = "MOCK"
    model: str = "mock-1"
    designer_provider: Optional[str] = None
    designer_model: Optional[str] = None
    temperature: float = 0.0
    timeout_seconds: int = 120
    
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    nvidia_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None
    base_url: Optional[str] = None

def get_llm_settings() -> LLMSettings:
    return LLMSettings(
        provider=os.getenv("PROMPTDOM_LLM_PROVIDER", "MOCK").upper(),
        model=os.getenv("PROMPTDOM_LLM_MODEL", "mock-1"),
        designer_provider=os.getenv("PROMPTDOM_LLM_DESIGNER_PROVIDER", "").upper() or None,
        designer_model=os.getenv("PROMPTDOM_LLM_DESIGNER_MODEL"),
        timeout_seconds=int(os.getenv("PROMPTDOM_LLM_TIMEOUT", "120")),
        openai_api_key=os.getenv("PROMPTDOM_LLM_OPENAI_API_KEY"),
        anthropic_api_key=os.getenv("PROMPTDOM_LLM_ANTHROPIC_API_KEY"),
        nvidia_api_key=os.getenv("PROMPTDOM_LLM_NVIDIA_API_KEY"),
        groq_api_key=os.getenv("PROMPTDOM_LLM_GROQ_API_KEY"),
        gemini_api_key=os.getenv("PROMPTDOM_LLM_GEMINI_API_KEY"),
        base_url=os.getenv("PROMPTDOM_LLM_BASE_URL"),
    )
