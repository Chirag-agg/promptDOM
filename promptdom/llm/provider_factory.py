from .base import BaseLLMProvider
from .providers.mock import MockProvider
from .providers.ollama import OllamaProvider
from .providers.lmstudio import LMStudioProvider
from ..config.llm import LLMSettings

class ProviderFactory:
    @staticmethod
    def get_provider(config: LLMSettings) -> BaseLLMProvider:
        provider = config.provider.upper()
        
        if provider == "MOCK":
            return MockProvider()
        elif provider == "OLLAMA":
            return OllamaProvider(model_name=config.model, timeout=config.timeout_seconds)
        elif provider == "LMSTUDIO":
            return LMStudioProvider(model_name=config.model, timeout=config.timeout_seconds)
        else:
            raise ValueError(f"Unknown LLM Provider: {provider}")
