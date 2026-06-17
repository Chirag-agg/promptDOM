from pydantic import BaseModel
import time
from .base import BaseLLMProvider

class HealthResponse(BaseModel):
    provider: str
    reachable: bool
    model: str
    latency_ms: float

class LLMHealthService:
    def __init__(self, provider: BaseLLMProvider, model_name: str, provider_name: str):
        self.provider = provider
        self.model_name = model_name
        self.provider_name = provider_name

    async def check_provider(self) -> HealthResponse:
        start_time = time.time()
        reachable = False
        try:
            # We perform a tiny generation to prove end-to-end reachability.
            await self.provider.generate(prompt="hi", max_tokens=1)
            reachable = True
        except Exception:
            pass
            
        latency_ms = (time.time() - start_time) * 1000
        
        return HealthResponse(
            provider=self.provider_name,
            reachable=reachable,
            model=self.model_name,
            latency_ms=latency_ms
        )
