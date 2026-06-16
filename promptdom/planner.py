import warnings
import asyncio
from typing import Dict, Optional
from .models import FeatureAction
from .planning.rule_planner import RulePlanner
from .planning.models import PlannerContext
from .inspection.models import CompactInspectionResponse

class PromptPlanner:
    """
    DEPRECATED: Use PlannerService and the new planning package instead.
    This class wraps RulePlanner to provide backward compatibility for existing tests/imports.
    """
    def __init__(self):
        warnings.warn("PromptPlanner is deprecated. Use PlannerService instead.", DeprecationWarning, stacklevel=2)
        self._rule_planner = RulePlanner()

    def parse_prompt(self, prompt: str) -> Optional[FeatureAction]:
        result = self.plan(prompt)
        if "error" in result:
            return None
        return FeatureAction(action=result["action"], target=result["target"])

    def plan(self, prompt: str) -> Dict:
        # Create a dummy context
        dummy_page_context = CompactInspectionResponse(
            title="", page_type="unknown", sections=[], visible_text_sample=""
        )
        context = PlannerContext(prompt=prompt, page_context=dummy_page_context)
        
        # Run async plan synchronously for backward compatibility
        try:
            loop = asyncio.get_running_loop()
            # If running in an event loop (e.g. from tests using pytest-asyncio or FastAPI),
            # we should avoid asyncio.run. However, the original plan() was synchronous.
            # A safe way is to create a new loop just for this if needed, or use the existing one if we can't block it.
            # Actually, since RulePlanner is fully synchronous in its implementation, we can just call it 
            # by awaiting it or creating a task. 
            # To be safest, we'll try to run it.
        except RuntimeError:
            pass
            
        # Since RulePlanner.plan is async but does no async I/O, we can just use asyncio.run safely if no loop
        # But if there is a loop, we can just instantiate the coroutine and run it.
        # Actually, let's just make RulePlanner.plan async and use a helper.
        
        # Helper to run async code synchronously in a thread if loop is running
        import concurrent.futures
        def _run_async():
            return asyncio.run(self._rule_planner.plan(context))
            
        try:
            asyncio.get_running_loop()
            with concurrent.futures.ThreadPoolExecutor() as pool:
                planner_result = pool.submit(_run_async).result()
        except RuntimeError:
            planner_result = asyncio.run(self._rule_planner.plan(context))

        if not planner_result.plans:
            return {
                "error": "Could not parse prompt. Supported actions: hide, show, highlight, unhighlight. Supported targets: youtube_shorts, comments, sidebar."
            }
            
        # Return the first plan for backward compatibility
        plan = planner_result.plans[0]
        return {
            "action": plan.action,
            "target": plan.target
        }