from pydantic import BaseModel
from ..llm.base import BaseLLMProvider
from ..compiler.models import FeatureSpec
from ..capabilities.registry import CapabilityRegistry

class FeatureSpecPlanner:
    def __init__(self, provider: BaseLLMProvider, capability_registry: CapabilityRegistry):
        self.provider = provider
        self.capability_registry = capability_registry

    async def plan(self, prompt: str) -> FeatureSpec:
        capabilities = self.capability_registry.list_all()
        supported = [k for k, v in capabilities.items() if v]
        
        system_prompt = (
            "You are a strict feature compiler. The user wants to manipulate a webpage. "
            "You MUST return a valid JSON object matching the requested FeatureSpec. "
            "Select the most appropriate actions based on the user's prompt. "
            "Make sure to provide 'name' for the feature and a list of 'actions'. "
            f"Currently Supported Capabilities: {', '.join(supported)}. "
            "Do NOT use actions for capabilities that are not supported."
        )
        
        # Pydantic Discriminator works natively when passed as a RootModel or Union
        # However, generate_structured expects a Type[T]. We'll use a dummy wrapper class
        # to ensure it parses properly.
        class Wrapper(BaseModel):
            spec: FeatureSpec
            
        wrapper_prompt = f"User Request: {prompt}\n\nPlease wrap the spec in a dictionary with a 'spec' key."
        result = await self.provider.generate_structured(
            prompt=wrapper_prompt,
            schema=Wrapper,
            system_prompt=system_prompt,
            temperature=0.0
        )
        
        return result.spec
