from typing import Optional
from .models import ActionPlan, PlannerContext
from ..llm.base import BaseLLMProvider

class LLMPlanner:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
        
    async def plan(self, context: PlannerContext) -> ActionPlan:
        system_prompt = (
            "You are a DOM planning engine. Your job is to convert the user's natural language "
            "prompt into a strict structured ActionPlan JSON. "
            "You must provide 'action', 'target' (a semantic description of the element), "
            "'target_type', 'confidence', and 'reasoning'. "
            "Never output markdown wrapping. Only output raw JSON matching the schema."
        )
        
        prompt = (
            f"User Prompt: {context.prompt}\n"
            f"Page Title: {context.page_context.title}\n"
            f"Page Type: {context.page_context.page_type}\n"
        )
        
        plan = await self.provider.generate_structured(
            prompt=prompt,
            schema=ActionPlan,
            system_prompt=system_prompt,
            temperature=0.0
        )
        
        plan.planner_source = "LLM"
        return plan
