from ..llm.base import BaseLLMProvider
from .models import DesignIntent

class IntentInterpreterService:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
        self.system_prompt = (
            "You are an expert UX architect. "
            "Your job is to translate a user's raw prompt into a set of core design principles. "
            "If the user asks to make the current website look like another specific website (e.g., 'Make YouTube like Netflix'), "
            "you MUST extract the name of the target website (e.g. 'netflix', 'x', 'twitter') and set it in 'target_website'. "
            "You MUST NOT mention any website-specific DOM elements, CSS selectors, or structural changes. "
            "Only output high-level principles that guide the redesign (e.g., 'reduce visual noise', 'increase focus on primary content', 'de-emphasize secondary navigation').\n"
            "Return JSON matching the requested schema."
        )

    async def interpret(self, prompt: str) -> DesignIntent:
        user_prompt = f"Extract design principles from this redesign request: '{prompt}'"
        return await self.provider.generate_structured(
            prompt=user_prompt,
            schema=DesignIntent,
            system_prompt=self.system_prompt,
            temperature=0.1
        )
