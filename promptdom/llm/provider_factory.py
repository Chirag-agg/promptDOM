from .base import BaseLLMProvider
from .providers.mock import MockProvider
from .providers.ollama import OllamaProvider
from .providers.nvidia import NvidiaNimProvider
from .providers.anthropic import AnthropicProvider
from .providers.groq import GroqProvider
from .providers.gemini import GeminiProvider
from ..config.llm import LLMSettings

class ProviderFactory:
    @staticmethod
    def _create_provider(provider: str, model: str, config: LLMSettings) -> BaseLLMProvider:
        if provider == "MOCK":
            return MockProvider()
        elif provider == "OLLAMA":
            return OllamaProvider(model_name=model, timeout=config.timeout_seconds)
        elif provider == "LMSTUDIO":
            return LMStudioProvider(model_name=model, timeout=config.timeout_seconds)
        elif provider == "ANTHROPIC":
            return AnthropicProvider(model_name=model, api_key=config.anthropic_api_key, timeout=config.timeout_seconds, base_url=config.base_url)
        elif provider == "NVIDIA":
            return NvidiaNimProvider(
                model_name=model, 
                api_key=config.nvidia_api_key, 
                timeout=config.timeout_seconds,
                base_url=config.base_url
            )
        elif provider == "GROQ":
            return GroqProvider(
                model_name=model, 
                api_key=config.groq_api_key, 
                timeout=config.timeout_seconds,
                base_url=config.base_url
            )
        elif provider == "GEMINI":
            return GeminiProvider(
                model_name=model, 
                api_key=config.gemini_api_key, 
                timeout=config.timeout_seconds,
                base_url=config.base_url
            )
        else:
            raise ValueError(f"Unknown LLM Provider: {provider}")

    @staticmethod
    def get_provider(config: LLMSettings) -> BaseLLMProvider:
        return ProviderFactory._create_provider(config.provider.upper(), config.model, config)

    @staticmethod
    def get_designer_provider(config: LLMSettings) -> BaseLLMProvider:
        provider = config.designer_provider if config.designer_provider else config.provider
        model = config.designer_model if config.designer_model else config.model
        return ProviderFactory._create_provider(provider.upper(), model, config)
