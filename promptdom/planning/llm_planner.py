from .base import BasePlanner
from .models import PlannerContext, PlannerResult

class LLMPlanner(BasePlanner):
    async def plan(self, context: PlannerContext) -> PlannerResult:
        """
        Placeholder for future LLM-based planning.
        """
        raise NotImplementedError("LLMPlanner is not yet implemented. Use RULE planner.")
