import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any

from .browser import BrowserManager
from .planner import PromptPlanner
from .runtime.engine import RuntimeEngine
from .models import ActionRequest, ActionResponse
from .inspection.service import InspectionService
from .inspection.models import InspectionResponse, CompactInspectionResponse, ResolutionInspectionResponse
from .visual.service import VisualInspectionService
from .visual.models import VisualInspectionResponse
from .planning.service import PlannerService
from .planning.models import PlannerResult, PlannerComparisonResponse, PlannerContext
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
from .analytics.models import PlannerAnalytics, PlannerComparisonLog, PlannerDisagreementMetrics
from .llm.health import LLMHealthService, HealthResponse
from .llm.models import LLMResponse
from .compiler.compiler import FeatureCompiler
from .compiler.models import FeatureSpec
from .planning.feature_spec_planner import FeatureSpecPlanner

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="PromptDOM", description="Local-first browser automation via natural language")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Global instances
browser_manager = BrowserManager()
runtime_engine = RuntimeEngine()
inspection_service = InspectionService(browser_manager)
analytics_collector = AnalyticsCollector()
visual_inspection_service = VisualInspectionService(browser_manager, inspection_service)
planner_service = PlannerService(inspection_service, analytics_collector)
semantic_resolver = SemanticResolver(inspection_service)
feature_store = FeatureStore()
feature_service = FeatureService(feature_store)
feature_matcher = FeatureMatcher(semantic_resolver)
feature_matching_service = FeatureMatchingService(feature_store, inspection_service, feature_matcher)
analytics_service = AnalyticsService(feature_store, analytics_collector)

llm_settings = get_llm_settings()
llm_provider = ProviderFactory.get_provider(llm_settings)
designer_provider = ProviderFactory.get_designer_provider(llm_settings)
llm_planner = LLMPlanner(llm_provider)
hybrid_planner = HybridPlannerService(planner_service, llm_planner, analytics_collector)
llm_health_service = LLMHealthService(llm_provider, llm_settings.model, llm_settings.provider)
feature_compiler = FeatureCompiler()

from .design.service import DesignPlanner
from .design.models import DesignPlan
design_planner = DesignPlanner(designer_provider)

from .capabilities.registry import CapabilityRegistry
capability_registry = CapabilityRegistry()
feature_spec_planner = FeatureSpecPlanner(llm_provider, capability_registry)

from .runtime.registry import RuntimeRegistry
from .runtime.lifecycle import LifecycleManager
from .runtime.service import RuntimeService
from .runtime.heartbeat import HeartbeatMonitor

runtime_registry = RuntimeRegistry()
lifecycle_manager = LifecycleManager(runtime_registry, browser_manager, analytics_collector)
runtime_service = RuntimeService(runtime_registry, lifecycle_manager, feature_compiler, feature_store, analytics_collector, browser_manager)
heartbeat_monitor = HeartbeatMonitor(browser_manager, runtime_registry, runtime_service)

from .transform.service import ExperimentalTransformationService
from .transform.executor import TransformExecutor
experimental_transformation_service = ExperimentalTransformationService(llm_provider, inspection_service)
transform_executor = TransformExecutor(browser_manager)

from .redesign.goal_analyzer import GoalAnalyzerService
from .redesign.evaluator import EvaluatorService
from .redesign.repair import RedesignRepairService
from .redesign.orchestrator import RedesignOrchestrator

goal_analyzer = GoalAnalyzerService(llm_provider)
evaluator = EvaluatorService(designer_provider)
redesign_repair_service = RedesignRepairService(semantic_resolver)

redesign_orchestrator = RedesignOrchestrator(
    browser=browser_manager,
    inspection_service=inspection_service,
    visual_service=visual_inspection_service,
    transform_service=experimental_transformation_service,
    transform_executor=transform_executor,
    goal_analyzer=goal_analyzer,
    evaluator=evaluator,
    repair_service=redesign_repair_service,
    design_planner=design_planner
)

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
        heartbeat_monitor.start()
        print("Heartbeat monitor started")
    except Exception as e:
        print(f"Warning: Could not initialize browser manager: {e}")
        print("Make sure Chrome is running with --remote-debugging-port=9222")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown"""
    heartbeat_monitor.stop()
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

@app.post("/plan/compare", response_model=PlannerComparisonResponse)
async def plan_prompt_compare(request: ActionRequest):
    """
    Compare planner engines, evaluating agreement and correctness against ground truth.
    """
    try:
        import time
        t0 = time.time()
        rule_result = await planner_service.get_plan(request.prompt)
        rule_latency = (time.time() - t0) * 1000
        
        t0 = time.time()
        try:
            page_context = await inspection_service.inspect_compact()
            llm_context = PlannerContext(prompt=request.prompt, page_context=page_context)
            llm_plan = await llm_planner.plan(llm_context)
            llm_result = PlannerResult(success=True, plans=[llm_plan])
        except Exception as e:
            llm_result = PlannerResult(success=False, failure_reason=str(e), plans=[])
        llm_latency = (time.time() - t0) * 1000
            
        best_rule = rule_result.plans[0] if rule_result.plans else None
        
        if best_rule and best_rule.confidence >= 0.80:
            winner = "RULE"
        else:
            if llm_result.success:
                winner = "LLM"
            else:
                winner = "RULE (fallback)"
        
        rule_target = best_rule.target if best_rule else ""
        llm_target = llm_result.plans[0].target if llm_result.plans else ""
        agreed = (rule_target == llm_target) and rule_target != ""
        
        import json
        import os
        ground_truth = None
        if os.path.exists("datasets/planning.json"):
            with open("datasets/planning.json", "r", encoding="utf-8") as f:
                dataset = json.load(f)
            for item in dataset:
                if item["prompt"] == request.prompt:
                    ground_truth = item["expected"]["plans"][0] if item["expected"].get("plans") else None
                    break
                    
        ground_truth_available = ground_truth is not None
        
        def is_correct(result: PlannerResult):
            if not ground_truth_available:
                return None
            plan = result.plans[0] if result.plans else None
            if not plan and not ground_truth:
                return True
            if not plan or not ground_truth:
                return False
            return plan.action == ground_truth["action"] and plan.target == ground_truth["target"]
            
        analytics_collector.log_planner_comparison(
            PlannerComparisonLog(
                prompt=request.prompt,
                rule_target=rule_target,
                llm_target=llm_target,
                agreed=agreed
            )
        )
        
        return PlannerComparisonResponse(
            rule=rule_result,
            llm=llm_result,
            hybrid={"selected": winner},
            agreement=agreed,
            winner=winner,
            ground_truth_available=ground_truth_available,
            rule_correct=is_correct(rule_result),
            llm_correct=is_correct(llm_result),
            hybrid_correct=is_correct(rule_result if "RULE" in winner else llm_result),
            rule_latency_ms=rule_latency,
            llm_latency_ms=llm_latency
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/llm/providers")
async def get_llm_providers():
    return {
        "available": ["MOCK", "OLLAMA", "LMSTUDIO"],
        "current": llm_settings.provider,
        "model": llm_settings.model
    }

@app.get("/llm/health", response_model=HealthResponse)
async def get_llm_health():
    return await llm_health_service.check_provider()

from .runtime.models import RuntimeFeature

@app.get("/runtime/features", response_model=list[RuntimeFeature])
async def list_runtime_features():
    return runtime_service.get_all_features()

@app.get("/capabilities")
async def get_capabilities():
    return capability_registry.list_all()

from .transform.models import TransformationRequest, GeneratedTransformation, TransformationPreviewResponse, TransformExecutionRequest, TransformExecutionResult, TransformTestResponse, TransformFeedbackRequest
from .analytics.models import TransformFeedbackLog

@app.post("/transform/design", response_model=DesignPlan)
async def generate_design_plan(request: TransformationRequest):
    try:
        inspection_data = await visual_inspection_service.capture_context()
        plan = await design_planner.generate_plan(request.prompt, inspection_data)
        
        # Log to telemetry
        analytics_collector.log_design_plan(request.prompt, plan)
        
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transform/experimental", response_model=GeneratedTransformation)
async def generate_experimental_transformation(request: TransformationRequest):
    try:
        inspection_data = await visual_inspection_service.capture_context()
        plan = await design_planner.generate_plan(request.prompt, inspection_data)
        return await experimental_transformation_service.generate_transformation(request.prompt, plan)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transform/preview", response_model=TransformationPreviewResponse)
async def generate_transformation_preview(request: TransformationRequest):
    try:
        inspection_data = await visual_inspection_service.capture_context()
        plan = await design_planner.generate_plan(request.prompt, inspection_data)
        
        # Log to telemetry
        analytics_collector.log_design_plan(request.prompt, plan)
        
        return await experimental_transformation_service.generate_preview(request.prompt, plan)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transform/apply", response_model=TransformExecutionResult)
async def apply_transformation(request: TransformExecutionRequest):
    preview = experimental_transformation_service.get_preview(request.transformation_id)
    if not preview:
        raise HTTPException(status_code=404, detail="Transformation preview not found")
        
    css_applied = await transform_executor.apply_css(request.transformation_id, preview.transformation.css)
    js_applied = await transform_executor.apply_javascript(request.transformation_id, preview.transformation.javascript)
    
    return TransformExecutionResult(
        transformation_id=request.transformation_id,
        success=True,
        applied_css=css_applied,
        applied_javascript=js_applied,
        message="Transformation applied successfully"
    )

@app.post("/transform/remove")
async def remove_transformation(request: TransformExecutionRequest):
    success = await transform_executor.remove_transformation(request.transformation_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to remove transformation")
    return {"status": "removed"}

@app.post("/transform/feedback")
async def log_transform_feedback(request: TransformFeedbackRequest):
    preview = experimental_transformation_service.get_preview(request.transformation_id)
    if not preview:
        raise HTTPException(status_code=404, detail="Transformation preview not found")
        
    log = TransformFeedbackLog(
        prompt=preview.prompt,
        design_plan=preview.design_plan,
        css=preview.transformation.css,
        javascript=preview.transformation.javascript,
        worked=request.worked,
        score=request.score,
        notes=request.notes,
        visual_context=None # We will populate this in Phase 8.2 once visual context is built
    )
    
    analytics_collector.log_transform_feedback(log)
    return {"status": "logged"}

@app.post("/transform/test", response_model=TransformTestResponse)
async def test_transformation(request: TransformationRequest):
    try:
        return await redesign_orchestrator.execute_redesign_loop(request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/runtime/features/{instance_id}/stop")
async def stop_runtime_feature(instance_id: str):
    success = await runtime_service.stop_feature(instance_id)
    if not success:
        raise HTTPException(status_code=404, detail="Feature instance not found or already stopped")
    return {"status": "stopped"}

@app.post("/runtime/features/{instance_id}/restart", response_model=RuntimeFeature)
async def restart_runtime_feature(instance_id: str):
    try:
        new_instance = await runtime_service.restart_feature(instance_id)
        if not new_instance:
            raise HTTPException(status_code=404, detail="Feature instance not found")
        return new_instance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class TestLLMRequest(BaseModel):
    prompt: str

@app.post("/llm/test", response_model=LLMResponse)
async def test_llm_provider(request: TestLLMRequest):
    try:
        return await llm_provider.generate(request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CompileRequest(BaseModel):
    feature_spec: dict

class ValidationResponse(BaseModel):
    valid: bool
    warnings: list[str]

@app.post("/compile")
async def compile_feature(request: CompileRequest):
    import time
    from .compiler.models import FeatureSpecAdapter
    from .analytics.models import FeatureCompilationLog
    try:
        t0 = time.time()
        # Parse dynamic union using a root model or type adapter
        from pydantic import TypeAdapter
        adapter = TypeAdapter(FeatureSpec)
        spec = adapter.validate_python(request.feature_spec)
        
        compiled = feature_compiler.compile(spec)
        latency = (time.time() - t0) * 1000
        
        analytics_collector.log_feature_compilation(FeatureCompilationLog(
            feature_type=spec.feature_type,
            success=True,
            compile_ms=latency
        ))
        
        return {
            "compiled": True,
            "javascript": compiled.javascript,
            "compiler_version": compiled.compiler_version
        }
    except Exception as e:
        latency = (time.time() - t0) * 1000 if 't0' in locals() else 0
        analytics_collector.log_feature_compilation(FeatureCompilationLog(
            feature_type=request.feature_spec.get("feature_type", "unknown"),
            success=False,
            compile_ms=latency
        ))
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/compile/validate", response_model=ValidationResponse)
async def validate_compile(request: CompileRequest):
    try:
        from pydantic import TypeAdapter
        adapter = TypeAdapter(FeatureSpec)
        spec = adapter.validate_python(request.feature_spec)
        feature_compiler.validator.validate(spec)
        return ValidationResponse(valid=True, warnings=[])
    except Exception as e:
        return ValidationResponse(valid=False, warnings=[str(e)])

class FeatureSpecRequest(BaseModel):
    prompt: str

@app.post("/feature-spec")
async def generate_feature_spec(request: FeatureSpecRequest):
    try:
        spec = await feature_spec_planner.plan(request.prompt)
        return {"feature_spec": spec.model_dump()}
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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

@app.get("/analytics/planner-disagreement", response_model=PlannerDisagreementMetrics)
async def get_planner_disagreement():
    return analytics_service.get_planner_disagreement()

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

@app.get("/visual/latest", response_model=VisualInspectionResponse)
async def get_latest_visual_context():
    """
    Returns the latest visual context, verifying screenshot and DOM capture.
    """
    return await visual_inspection_service.capture_context()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)