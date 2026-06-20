from ..llm.base import BaseLLMProvider
from .models import GoalAnalysis

class GoalAnalyzerService:
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm = llm_provider
        self.system_prompt = """You are an expert UX/UI goal analyzer.
Your job is to analyze a user's prompt for redesigning a web page and determine the primary and secondary goals.

Valid Goal Types:
- DECLUTTER: Removing noise, simplifying the interface.
- REMOVE_ELEMENT: Hiding or deleting a specific named element.
- RESTYLE: Changing colors, fonts, borders, shadows, etc.
- LAYOUT_CHANGE: Changing the position, alignment, or structure of elements.
- REORGANIZE: Moving elements into a different logical order.

Analyze the prompt and output a JSON object matching the requested schema exactly.
CRITICAL RULES FOR JSON ARRAY:
- MAXIMUM 3 items in the `secondary_goals` array.
- DO NOT repeat goals. Every item must be unique.
- Stop generating after 3 items.
"""

    async def analyze(self, prompt: str) -> GoalAnalysis:
        user_prompt = f"Analyze this redesign request: '{prompt}'"
        return await self.llm.generate_structured(
            prompt=user_prompt,
            schema=GoalAnalysis,
            system_prompt=self.system_prompt,
            temperature=0.0
        )
