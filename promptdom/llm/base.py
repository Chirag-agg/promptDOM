from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar
from pydantic import BaseModel
from .models import LLMResponse, ProviderCapabilities

T = TypeVar('T', bound=BaseModel)

class BaseLLMProvider(ABC):
    @property
    @abstractmethod
    def capabilities(self) -> ProviderCapabilities:
        pass

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1000
    ) -> T:
        """
        Structured generation for planners.
        Providers should return an instance of the provided Pydantic schema.
        """
        pass
