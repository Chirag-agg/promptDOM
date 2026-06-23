from ..llm.base import BaseLLMProvider
from ..intent.models import DesignIntent, ImpactAnalysis
from ..knowledge.query import FilteredContext

class ImpactAnalyzerService:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
        self.system_prompt = (
            "You are a strategic UX impact analyzer. "
            "The concepts you receive represent STRUCTURAL UI REGIONS of the site "
            "(e.g., 'shorts', 'sidebar', 'feed', 'guide') — NOT individual content items. "
            "Your job is to determine which structural regions violate the design intent. "
            "NEVER target concepts that are core functionality (video_player, search, header). "
            "Only target decorative or secondary regions like shorts, chips_bar, notifications, guide. "
            "Return JSON matching the requested schema."
        )

    async def analyze(self, intent: DesignIntent, context: FilteredContext) -> ImpactAnalysis:
        user_prompt = (
            f"Design Intent Principles:\n"
            f"{chr(10).join(f'- {p}' for p in intent.principles)}\n\n"
            f"Relevant Concepts on the page:\n"
            f"{', '.join(context.concepts)}\n\n"
            "Analyze the impact each concept has on the design principles and output the required changes."
        )
        
        return await self.provider.generate_structured(
            prompt=user_prompt,
            schema=ImpactAnalysis,
            system_prompt=self.system_prompt,
            temperature=0.1
        )
