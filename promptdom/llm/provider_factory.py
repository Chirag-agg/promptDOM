from .base import BaseLLMProvider
from .providers.mock import MockProvider
from .providers.ollama import OllamaProvider
from .providers.openai import OpenAIProvider
from .providers.anthropic import AnthropicProvider
from .providers.gemini import GeminiProvider
from .providers.openrouter import OpenRouterProvider
from .providers.lmstudio import LMStudioProvider
from ..config.llm import LLMSettings

class ProviderFactory:
    @staticmethod
    def get_provider(config: LLMSettings) -> BaseLLMProvider:
        provider = config.provider.upper()
        
        if provider == "MOCK":
            return MockProvider()
        elif provider == "OLLAMA":
            return OllamaProvider()
        elif provider == "OPENAI":
            return OpenAIProvider()
        elif provider == "ANTHROPIC":
            return AnthropicProvider()
        elif provider == "GEMINI":
            return GeminiProvider()
        elif provider == "OPENROUTER":
            return OpenRouterProvider()
        elif provider == "LMSTUDIO":
            return LMStudioProvider()
        else:
            raise ValueError(f"Unknown LLM Provider: {provider}")
