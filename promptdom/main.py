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
from .inspection.exceptions import BrowserUnavailableError, NoActivePageError, PageClosedError


app = FastAPI(title="PromptDOM", description="Local-first browser automation via natural language")

# Global instances
browser_manager = BrowserManager()
runtime_engine = RuntimeEngine()
inspection_service = InspectionService(browser_manager)
planner_service = PlannerService(inspection_service)
semantic_resolver = SemanticResolver(inspection_service)

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