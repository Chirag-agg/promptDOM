import asyncio
import json
import time

from promptdom.inspection.models import CompactInspectionResponse
from promptdom.planning.models import PlannerContext
from promptdom.planning.service import PlannerService
from promptdom.planning.llm_planner import LLMPlanner
from promptdom.planning.hybrid_planner import HybridPlannerService
from promptdom.llm.providers.mock import MockProvider
from promptdom.analytics.collector import AnalyticsCollector

class MockInspectionService:
    async def inspect_compact(self):
        return CompactInspectionResponse(
            title="Mock Page",
            page_type="mock",
            visible_text_sample="",
            sections=[]
        )

async def main():
    with open("datasets/planning.json", "r", encoding="utf-8") as f:
        dataset = json.load(f)

    inspection = MockInspectionService()
    analytics = AnalyticsCollector(data_dir="data_benchmark")
    
    rule_planner = PlannerService(inspection, analytics)
    llm_provider = MockProvider()
    llm_planner = LLMPlanner(llm_provider)
    hybrid_planner = HybridPlannerService(rule_planner, llm_planner, analytics)

    print(f"Loaded {len(dataset)} items from planning.json")
    
    for engine_name, engine_func in [
        ("RulePlanner", lambda p: rule_planner.get_plan(p)),
        ("LLMPlanner", lambda p: llm_planner.plan(PlannerContext(prompt=p, page_context=CompactInspectionResponse(title="M", page_type="mock", visible_text_sample="", sections=[])))),
        ("HybridPlanner", lambda p: hybrid_planner.get_plan(p))
    ]:
        print(f"\nEvaluating {engine_name}...")
        correct = 0
        total_latency = 0.0
        
        fallback_count = 0

        for item in dataset:
            prompt = item["prompt"]
            expected = item["expected"]

            start = time.time()
            try:
                result = await engine_func(prompt)
                
                # Rule and Hybrid return PlannerResult, LLM returns ActionPlan directly
                if hasattr(result, "plans"):
                    plan = result.plans[0] if result.plans else None
                else:
                    plan = result

                if plan:
                    match = (plan.action == expected["action"] and plan.target == expected["target"])
                    if match:
                        correct += 1
                        
                    if getattr(plan, "planner_source", "") == "HYBRID_LLM":
                        fallback_count += 1
                        
            except Exception as e:
                print(f"Error evaluating '{prompt}': {e}")
            
            latency = (time.time() - start) * 1000
            total_latency += latency
            
        print(f"Accuracy: {correct}/{len(dataset)} ({(correct/len(dataset))*100:.1f}%)")
        print(f"Average Latency: {total_latency/len(dataset):.2f}ms")
        if engine_name == "HybridPlanner":
            print(f"Fallback to LLM Count: {fallback_count}")

if __name__ == "__main__":
    asyncio.run(main())
