from ..llm.base import BaseLLMProvider
from ..intent.models import ImpactAnalysis, TransformationDelta

class TransformationPlannerService:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
        self.system_prompt = (
            "You are a structural transformation planner. "
            "Your job is to convert strategic impact analysis (e.g., DEEMPHASIZE 'Shorts') into concrete structural operations (e.g., COLLAPSE 'Shorts', or REMOVE 'Shorts'). "
            "You must map every concept impact into one or more concrete DOM-level operations. "
            "Valid operations are: REMOVE, COLLAPSE, RESTYLE, ADD, PRIORITIZE. "
            "Return JSON matching the requested schema. DO NOT generate CSS or Javascript."
        )

    async def plan(self, analysis: ImpactAnalysis) -> TransformationDelta:
        user_prompt = (
            f"Impact Analysis:\n"
            f"{analysis.model_dump_json(indent=2)}\n\n"
            "Generate the concrete transformation operations required to achieve these impacts."
        )
        
        return await self.provider.generate_structured(
            prompt=user_prompt,
            schema=TransformationDelta,
            system_prompt=self.system_prompt,
            temperature=0.1
        )
