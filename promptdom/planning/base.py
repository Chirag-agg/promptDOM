from abc import ABC, abstractmethod
from .models import PlannerContext, PlannerResult

class BasePlanner(ABC):
    @abstractmethod
    async def plan(self, context: PlannerContext) -> PlannerResult:
        """Analyze the context and return a plan"""
        pass
