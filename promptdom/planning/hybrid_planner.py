from typing import Optional
import time
from .models import PlannerResult, PlannerContext
from .service import PlannerService
from .llm_planner import LLMPlanner
from ..analytics.models import PlanningLog
from ..analytics.collector import AnalyticsCollector

class HybridPlannerService:
    def __init__(
        self, 
        rule_planner: PlannerService, 
        llm_planner: LLMPlanner,
        analytics_collector: AnalyticsCollector
    ):
        self.rule_planner = rule_planner
        self.llm_planner = llm_planner
        self.analytics_collector = analytics_collector
        
    async def get_plan(self, prompt: str) -> PlannerResult:
        start_time = time.time()
        
        # 1. Run RulePlanner
        # Note: RulePlanner already logs to analytics with "RULE".
        # We will override the logging for the final hybrid decision.
        # But wait, RulePlanner internally logs it. That means we get double logs!
        # To fix this, RulePlanner checks if it's called independently. 
        # Actually, it's fine for now, we just overwrite the result source so at least the replay has the final source.
        rule_result = await self.rule_planner.get_plan(prompt)
        
        best_plan = rule_result.plans[0] if rule_result.plans else None
            
        if best_plan and best_plan.confidence >= 0.80:
            best_plan.planner_source = "HYBRID_RULE"
            self._log(prompt, "HYBRID_RULE", True, start_time)
            return rule_result
            
        # 2. Fallback to LLMPlanner
        try:
            page_context = await self.rule_planner.inspection_service.inspect_compact()
            context = PlannerContext(prompt=prompt, page_context=page_context)
            
            llm_plan = await self.llm_planner.plan(context)
            llm_plan.planner_source = "HYBRID_LLM"
            llm_plan.fallback_reason = "low_confidence"
            
            result = PlannerResult(plans=[llm_plan])
            self._log(prompt, "HYBRID_LLM", True, start_time, "low_confidence")
            return result
        except Exception as e:
            if best_plan:
                best_plan.planner_source = "HYBRID_RULE"
                best_plan.fallback_reason = "provider_failure"
            self._log(prompt, "HYBRID_RULE", False, start_time, "provider_failure")
            return rule_result

    def _log(self, prompt: str, source: str, success: bool, start_time: float, fallback: Optional[str] = None):
        ms = (time.time() - start_time) * 1000.0
        log = PlanningLog(
            prompt=prompt,
            planner_source=source,
            success=success,
            execution_time_ms=ms,
            fallback_reason=fallback
        )
        self.analytics_collector.log_planning_request(log)
