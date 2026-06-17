import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any

from .browser import BrowserManager
from .planner import PromptPlanner
from .runtime import RuntimeEngine
from .models import ActionRequest, ActionResponse
from .inspection.service import InspectionService
from .inspection.models import InspectionResponse, CompactInspectionResponse, ResolutionInspectionResponse
from .planning.service import PlannerService
from .planning.models import PlannerResult
from .resolution.resolver import SemanticResolver
from .resolution.models import ResolutionResult
from .features.store import FeatureStore
from .features.service import FeatureService
from .features.models import Feature, FeatureCreate
from .features.matching_models import MatchResult, DiagnosticsResult
from .features.matcher import FeatureMatcher
from .features.matching_service import FeatureMatchingService
from .features.auto_apply_models import AutoApplyResult
from .features.auto_apply import AutoApplyService
from .repair.models import RepairResult
from .repair.updater import SelectorVerifier
from .resolution.candidates import CandidateBuilder
from .repair.service import FeatureRepairService
from .analytics.models import FeatureAnalytics, SiteAnalytics, SystemHealth, FeatureTimeline, RecentAnalytics
from .analytics.collector import AnalyticsCollector
from .analytics.service import AnalyticsService
from .inspection.exceptions import BrowserUnavailableError, NoActivePageError, PageClosedError
from .config.llm import get_llm_settings
from .llm.provider_factory import ProviderFactory
from .planning.llm_planner import LLMPlanner
from .planning.hybrid_planner import HybridPlannerService
from .analytics.models import PlannerAnalytics


app = FastAPI(title="PromptDOM", description="Local-first browser automation via natural language")

# Global instances
browser_manager = BrowserManager()
runtime_engine = RuntimeEngine()
inspection_service = InspectionService(browser_manager)
analytics_collector = AnalyticsCollector()
planner_service = PlannerService(inspection_service, analytics_collector)
semantic_resolver = SemanticResolver(inspection_service)
feature_store = FeatureStore()
feature_service = FeatureService(feature_store)
feature_matcher = FeatureMatcher(semantic_resolver)
feature_matching_service = FeatureMatchingService(feature_store, inspection_service, feature_matcher)
analytics_service = AnalyticsService(feature_store, analytics_collector)

llm_settings = get_llm_settings()
llm_provider = ProviderFactory.get_provider(llm_settings)
llm_planner = LLMPlanner(llm_provider)
hybrid_planner = HybridPlannerService(planner_service, llm_planner, analytics_collector)

auto_apply_service = AutoApplyService(
    matching_service=feature_matching_service,
    store=feature_store,
    runtime=runtime_engine,
    inspection_service=inspection_service,
    browser_manager=browser_manager,
    analytics_collector=analytics_collector
)
candidate_builder = CandidateBuilder()
selector_verifier = SelectorVerifier(candidate_builder)
feature_repair_service = FeatureRepairService(
    store=feature_store,
    inspection_service=inspection_service,
    resolver=semantic_resolver,
    verifier=selector_verifier,
    analytics_collector=analytics_collector
)

# Deprecated planner instance for backward compatibility if needed internally
planner = PromptPlanner()

# Exception handlers
@app.exception_handler(BrowserUnavailableError)
async def browser_unavailable_exception_handler(request, exc):
    return JSONResponse(status_code=503, content={"detail": str(exc)})

@app.exception_handler(NoActivePageError)
async def no_active_page_exception_handler(request, exc):
    return JSONResponse(status_code=404, content={"detail": str(exc)})

@app.exception_handler(PageClosedError)
async def page_closed_exception_handler(request, exc):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.on_event("startup")
async def startup_event():
    """Initialize browser connection on startup"""
    try:
        await browser_manager.initialize()
        print("Browser manager initialized successfully")
    except Exception as e:
        print(f"Warning: Could not initialize browser manager: {e}")
        print("Make sure Chrome is running with --remote-debugging-port=9222")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    await browser_manager.cleanup()


@app.post("/plan", response_model=PlannerResult)
async def plan_prompt(request: ActionRequest):
    """
    Perform context-aware planning for a natural language prompt.
    Returns structured action plans without executing them.
    """
    try:
        return await planner_service.get_plan(request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/plan/hybrid", response_model=PlannerResult)
async def plan_prompt_hybrid(request: ActionRequest):
    """
    Perform context-aware planning for a natural language prompt using HybridPlanner.
    """
    try:
        return await hybrid_planner.get_plan(request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from pydantic import BaseModel
class ResolveRequest(BaseModel):
    target: str
    target_type: str = "unknown"

@app.post("/resolve", response_model=ResolutionResult)
async def resolve_target(request: ResolveRequest):
    """
    Resolve a human-readable target description into a concrete DOM selector.
    """
    try:
        return await semantic_resolver.resolve(request.target, request.target_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute", response_model=ActionResponse)
async def execute_prompt(request: ActionRequest):
    """
    Execute a natural language prompt on the active browser tab
    """
    try:
        # 1. Get the action plan from the planner service
        planner_result = await planner_service.get_plan(request.prompt)
        
        if not planner_result.plans:
            raise HTTPException(status_code=400, detail="Could not generate a valid plan for the prompt.")
            
        # 2. Extract the plans
        plans = planner_result.plans
        
        # 3. Execute the actions
        success = True
        executed_actions = []
        for plan in plans:
            # Resolve the target to a CSS selector
            resolution = await semantic_resolver.resolve(plan.target, plan.target_type)
            if not resolution.matched:
                raise HTTPException(status_code=400, detail=f"Could not resolve target '{plan.target}': {resolution.explanation}")
                
            # Execute with the resolved selector
            action_success = await runtime_engine.execute(plan.action, resolution.selector, browser_manager)
            success = success and action_success
            if action_success:
                executed_actions.append(f"{plan.action} on {plan.target} ({resolution.selector})")
                
        return ActionResponse(
            success=success,
            action={"action": plans[0].action, "target": plans[0].target}, # Return first for backward compatibility
            message=f"Successfully executed: {', '.join(executed_actions)}" if success else "Some or all actions failed."
        )

# Feature Endpoints
from typing import List

@app.post("/features", response_model=Feature)
async def create_feature(feature: FeatureCreate):
    try:
        return feature_service.create_feature(feature)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/features", response_model=List[Feature])
async def list_features():
    return feature_service.list_features()

@app.get("/features/matches", response_model=MatchResult)
async def get_feature_matches():
    """
    Evaluate all stored features against the current page to determine which apply.
    """
    try:
        return await feature_matching_service.get_matches()
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/features/diagnostics", response_model=DiagnosticsResult)
async def get_feature_diagnostics():
    """
    Returns high-level health information about all stored features against the active page.
    """
    try:
        return await feature_matching_service.get_diagnostics()
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/features/apply", response_model=AutoApplyResult)
async def auto_apply_features(dry_run: bool = False):
    """
    Automatically apply ready features to the current page.
    If dry_run is True, returns what would be applied without executing.
    """
    try:
        return await auto_apply_service.apply_features(dry_run=dry_run)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/features/stale", response_model=List[Feature])
async def get_stale_features():
    """
    Returns features that are stale on the current page.
    """
    try:
        return await feature_repair_service.get_stale_features()
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/features/repair", response_model=RepairResult)
async def repair_features(dry_run: bool = False):
    """
    Attempts to deterministically repair all stale features on the active page.
    """
    try:
        return await feature_repair_service.repair_features(dry_run=dry_run)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/features/{feature_id}/timeline", response_model=FeatureTimeline)
async def get_feature_timeline(feature_id: str):
    """
    Returns an audit log of all repairs and applications performed for a given feature.
    """
    try:
        return analytics_service.get_feature_timeline(feature_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/analytics/features", response_model=List[FeatureAnalytics])
async def get_feature_analytics():
    return analytics_service.get_feature_analytics()

@app.get("/analytics/planners", response_model=PlannerAnalytics)
async def get_planner_analytics():
    return analytics_service.get_planner_analytics()

@app.get("/analytics/sites", response_model=List[SiteAnalytics])
async def get_site_analytics():
    return analytics_service.get_site_analytics()

@app.get("/analytics/health", response_model=SystemHealth)
async def get_system_health():
    return analytics_service.get_system_health()

@app.get("/analytics/recent", response_model=RecentAnalytics)
async def get_recent_events():
    return analytics_service.get_recent_events()

@app.get("/features/{feature_id}", response_model=Feature)
async def get_feature(feature_id: str):
    f = feature_service.get_feature(feature_id)
    if not f:
        raise HTTPException(status_code=404, detail="Feature not found")
    return f

@app.delete("/features/{feature_id}")
async def delete_feature(feature_id: str):
    if not feature_service.delete_feature(feature_id):
        raise HTTPException(status_code=404, detail="Feature not found")
    return {"status": "deleted"}

@app.patch("/features/{feature_id}/toggle", response_model=Feature)
async def toggle_feature(feature_id: str):
    f = feature_service.toggle_feature(feature_id)
    if not f:
        raise HTTPException(status_code=404, detail="Feature not found")
    return f

class FromPromptRequest(BaseModel):
    prompt: str

@app.post("/features/from-prompt", response_model=Feature)
async def create_feature_from_prompt(request: FromPromptRequest):
    """
    Generate a feature from a natural language prompt without executing it.
    """
    try:
        planner_result = await planner_service.get_plan(request.prompt)
        if not planner_result.plans:
            raise HTTPException(status_code=400, detail="Could not generate a valid plan for the prompt.")
            
        plan = planner_result.plans[0]
        resolution = await semantic_resolver.resolve(plan.target, plan.target_type)
        if not resolution.matched:
            raise HTTPException(status_code=400, detail=f"Could not resolve target '{plan.target}': {resolution.explanation}")
            
        page_info = await browser_manager.get_active_tab_info()
        
        feature_data = FeatureCreate(
            name=f"{plan.action.capitalize()} {plan.target.capitalize()}",
            prompt=request.prompt,
            source="planner",
            hostname=page_info.get("hostname", "unknown") if page_info else "unknown",
            page_type="unknown",
            target=plan.target,
            target_type=plan.target_type,
            action=plan.action,
            selector=resolution.selector
        )
        
        return feature_service.create_feature(feature_data)
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "PromptDOM"}

@app.get("/inspect", response_model=InspectionResponse)
async def inspect_page():
    """
    Get deep structured inspection of the currently active page.
    """
    return await inspection_service.inspect()

@app.get("/inspect/compact", response_model=CompactInspectionResponse)
async def inspect_page_compact():
    """
    Get a lightweight subset of page context, ideal for local LLMs.
    """
    return await inspection_service.inspect_compact()

@app.get("/inspect/resolution", response_model=ResolutionInspectionResponse)
async def inspect_page_resolution():
    """
    Get just the DOM snapshot required for semantic target resolution.
    """
    return await inspection_service.inspect_resolution()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)