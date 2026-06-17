import os
import json
import urllib.parse
from datetime import datetime
import time
from .models import PlannerContext, PlannerResult
from .rule_planner import RulePlanner
from .llm_planner import LLMPlanner
from ..inspection.service import InspectionService
from ..analytics.collector import AnalyticsCollector
from ..analytics.models import PlanningLog

class PlannerService:
    def __init__(self, inspection_service: InspectionService, analytics_collector: AnalyticsCollector = None):
        self.inspection_service = inspection_service
        self.analytics_collector = analytics_collector
        self.planner_type = "RULE"
        self.log_file = "planner_replay.jsonl"
        self.planner = RulePlanner()

    async def get_plan(self, prompt: str) -> PlannerResult:
        start_time = time.time()
        # 1. Obtain page context
        page_context = await self.inspection_service.inspect_compact()
        
        # 2. Build PlannerContext
        context = PlannerContext(
            prompt=prompt,
            page_context=page_context
        )
        
        # 3. Execute selected planner
        result = await self.planner.plan(context)
        
        # Log to Analytics
        if self.analytics_collector and result.plans:
            # default to RULE if not set
            source = result.plans[0].planner_source
            ms = (time.time() - start_time) * 1000.0
            self.analytics_collector.log_planning_request(
                PlanningLog(
                    prompt=prompt,
                    planner_source=source,
                    success=True,
                    execution_time_ms=ms,
                    fallback_reason=result.plans[0].fallback_reason
                )
            )
        
        # 4. Log the replay data
        await self._log_replay(prompt, page_context, result)
        
        # 5. Return PlannerResult
        return result

    async def _log_replay(self, prompt: str, page_context, result: PlannerResult):
        # Extract URL and Hostname dynamically since Compact context doesn't have them
        try:
            active_page = await self.inspection_service.browser_manager.get_active_page()
            url = active_page.url
            hostname = urllib.parse.urlparse(url).hostname or ""
        except Exception:
            url = ""
            hostname = ""
            
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "prompt": prompt,
            "url": url,
            "hostname": hostname,
            "page_type": page_context.page_type,
            "planner": self.planner_type,
            "context_summary": {
                "title": page_context.title,
                "sections": [{"role": s.role, "identifier": s.identifier} for s in page_context.sections]
            },
            "result": result.model_dump()
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry) + "\\n")
        except Exception as e:
            print(f"Warning: Could not write to replay log: {e}")
