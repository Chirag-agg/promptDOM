import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
from typing import Dict, Any, List

from .browser import BrowserManager
from .inspection.service import InspectionService
from .inspection.exceptions import BrowserUnavailableError, NoActivePageError, PageClosedError
from .visual.service import VisualInspectionService
from .analytics.collector import AnalyticsCollector
from .config.llm import get_llm_settings
from .llm.provider_factory import ProviderFactory
from .llm.health import LLMHealthService, HealthResponse

from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(title="PromptDOM", description="Local-first browser automation via natural language")

os.makedirs("data", exist_ok=True)
app.mount("/data", StaticFiles(directory="data"), name="data")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
browser_manager = BrowserManager()
inspection_service = InspectionService(browser_manager)
analytics_collector = AnalyticsCollector()
visual_inspection_service = VisualInspectionService(browser_manager, inspection_service)

llm_settings = get_llm_settings()
llm_provider = ProviderFactory.get_provider(llm_settings)
designer_provider = ProviderFactory.get_designer_provider(llm_settings)
llm_health_service = LLMHealthService(llm_provider, llm_settings.model, llm_settings.provider)

from .intent.interpreter import IntentInterpreterService
from .knowledge.query import GraphQueryEngine
from .planning.impact_analyzer import ImpactAnalyzerService
from .planning.transformation_planner import TransformationPlannerService
from .transform.engineer import CSSJSEngineerService
from .transform.executor import TransformExecutor

intent_interpreter = IntentInterpreterService(llm_provider)
graph_query_engine = GraphQueryEngine(llm_provider)
impact_analyzer = ImpactAnalyzerService(llm_provider)
transformation_planner = TransformationPlannerService(llm_provider)
css_js_engineer = CSSJSEngineerService(llm_provider, inspection_service)
transform_executor = TransformExecutor(browser_manager)

from .history.service import HistoryService
history_service = HistoryService()

from .capture.storage import CaptureStorage
from .capture.service import CaptureService
from .capture.models import SiteSnapshot
from .intelligence.service import IntelligenceService
from .archetypes.service import ArchetypeService
from .knowledge.service import KnowledgeService

capture_storage = CaptureStorage()
capture_service = CaptureService(browser_manager, capture_storage)
intelligence_service = IntelligenceService()
archetype_service = ArchetypeService()
knowledge_service = KnowledgeService(capture_storage, intelligence_service, archetype_service)

from .redesign.orchestrator import RedesignOrchestrator
redesign_orchestrator = RedesignOrchestrator(
    browser=browser_manager,
    inspection_service=inspection_service,
    visual_service=visual_inspection_service,
    transform_executor=transform_executor,
    intent_interpreter=intent_interpreter,
    graph_query_engine=graph_query_engine,
    impact_analyzer=impact_analyzer,
    transformation_planner=transformation_planner,
    css_js_engineer=css_js_engineer,
    knowledge_service=knowledge_service,
    history_service=history_service
)

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

@app.get("/browser/screenshot")
async def get_browser_screenshot():
    try:
        # full_page=False is faster and matches the live viewport the user actually sees
        image_bytes = await browser_manager.take_screenshot(full_page=False)
        return Response(content=image_bytes, media_type="image/png")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from .transform.models import (
    TransformationRequest, TransformExecutionRequest, TransformTestResponse, 
    TransformFeedbackRequest, ApplyRedesignRequest
)

@app.post("/transform/remove")
async def remove_transformation(request: TransformExecutionRequest):
    success = await transform_executor.remove_transformation(request.transformation_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to remove transformation")
    return {"status": "removed"}

from .transform.models import PlanRequest
from .design.models import DesignPlan

@app.post("/transform/plan", response_model=DesignPlan)
async def generate_design_plan(request: PlanRequest):
    try:
        return await redesign_orchestrator.generate_plan(request.prompt)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transform/apply", response_model=TransformTestResponse)
async def apply_transformation_plan(request: ApplyRedesignRequest):
    try:
        return await redesign_orchestrator.apply_redesign(request.prompt, getattr(request, 'design_plan', None))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

from .history.models import TransformationHistoryRecord

@app.get("/history", response_model=list[TransformationHistoryRecord])
async def list_history():
    try:
        return history_service.list_records()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{run_id}", response_model=TransformationHistoryRecord)
async def get_history_record(run_id: str):
    record = history_service.get_record(run_id)
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record

@app.get("/capture")
async def capture_site():
    try:
        snapshot = await capture_service.capture_current_page()
        return snapshot
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/capture/list", response_model=list[SiteSnapshot])
async def list_snapshots():
    try:
        return capture_storage.list_snapshots()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/capture/{snapshot_id}", response_model=SiteSnapshot)
async def get_snapshot(snapshot_id: str):
    snapshot = capture_storage.load_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot

@app.post("/intelligence/{snapshot_id}")
async def analyze_snapshot(snapshot_id: str, force: bool = False):
    snapshot = capture_storage.load_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    try:
        model = intelligence_service.analyze(snapshot, force=force)
        return model
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/archetype/{snapshot_id}")
async def get_snapshot_archetype(snapshot_id: str):
    snapshot = capture_storage.load_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    try:
        model = intelligence_service.analyze(snapshot, force=False)
        archetype = archetype_service.detect(snapshot, model)
        return archetype
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge", response_model=list[str])
async def list_knowledge_packs():
    try:
        packs = knowledge_service.list_packs()
        return [p.hostname for p in packs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/knowledge/{hostname}")
async def get_knowledge_pack(hostname: str):
    pack = knowledge_service.get_pack(hostname)
    if not pack:
        raise HTTPException(status_code=404, detail="Pack not found")
    return pack

@app.post("/knowledge/build/{hostname}")
async def build_knowledge_pack(hostname: str):
    try:
        pack = knowledge_service.build_pack(hostname)
        if not pack:
            raise HTTPException(status_code=500, detail="Failed to build knowledge pack")
        return pack
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/knowledge/build")
async def build_knowledge_pack_auto():
    try:
        snapshot = await capture_service.capture_current_page()
        return {"status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))