from typing import Optional
from ..browser import BrowserManager
from ..inspection.service import InspectionService
from ..visual.service import VisualInspectionService
from ..transform.executor import TransformExecutor
from ..transform.models import TransformTestResponse, TransformExecutionResult
from .models import IterationContext, IterationRecord

from ..intent.interpreter import IntentInterpreterService
from ..knowledge.query import GraphQueryEngine
from ..planning.impact_analyzer import ImpactAnalyzerService
from ..planning.transformation_planner import TransformationPlannerService
from ..transform.engineer import CSSJSEngineerService
from ..knowledge.service import KnowledgeService
from ..intent.models import PipelineTrace

class RedesignOrchestrator:
    def __init__(
        self,
        browser: BrowserManager,
        inspection_service: InspectionService,
        visual_service: VisualInspectionService,
        transform_executor: TransformExecutor,
        intent_interpreter: IntentInterpreterService,
        graph_query_engine: GraphQueryEngine,
        impact_analyzer: ImpactAnalyzerService,
        transformation_planner: TransformationPlannerService,
        css_js_engineer: CSSJSEngineerService,
        knowledge_service: KnowledgeService,
        history_service=None
    ):
        self.browser = browser
        self.inspection_service = inspection_service
        self.visual_service = visual_service
        self.transform_executor = transform_executor
        
        self.intent_interpreter = intent_interpreter
        self.graph_query_engine = graph_query_engine
        self.impact_analyzer = impact_analyzer
        self.transformation_planner = transformation_planner
        
        from ..planning.cross_site_planner import CrossSitePlannerService
        self.cross_site_planner = CrossSitePlannerService(self.transformation_planner.provider)
        
        from ..utils.domain import DomainResolver
        self.domain_resolver = DomainResolver()
        
        self.css_js_engineer = css_js_engineer
        self.knowledge_service = knowledge_service
        
        self.history_service = history_service
        self.max_iterations = 3
        self.min_improvement = 0.05

    async def generate_plan(self, prompt: str):
        from ..design.models import DesignPlan
        system_prompt = (
            "You are an expert UX/UI designer planning a website redesign. "
            "Given the user's prompt, create a comprehensive DesignPlan matching the requested schema. "
            "Detail the specific changes (REMOVE, RESTYLE, ADD, MOVE) that need to be made."
        )
        user_prompt = f"User Request: {prompt}\n\nPlease generate the DesignPlan."
        
        return await self.transformation_planner.provider.generate_structured(
            prompt=user_prompt,
            schema=DesignPlan,
            system_prompt=system_prompt,
            temperature=0.7
        )

    async def apply_redesign(self, prompt: str, _deprecated_plan=None) -> TransformTestResponse:
        # Phase 10 Execution Pipeline
        
        # Capture Initial State
        initial_visual = await self.visual_service.capture_context()
        initial_dom = await self.inspection_service.inspect_compact()
        
        # 1. Fetch Knowledge Pack (Fallback)
        print("2. Fetching Knowledge Pack...")
        import urllib.parse
        hostname = urllib.parse.urlparse(initial_visual.page_context.url).hostname
        pack = self.knowledge_service.get_pack(hostname)
        if not pack:
            pack = self.knowledge_service.build_pack(hostname)
            
        # 10.0 Intent Interpreter
        intent = await self.intent_interpreter.interpret(prompt)
        
        # 10.1 & 10.2 & 10.3 Core Planning
        if intent.target_website:
            print(f"Cross-Site Target Detected: {intent.target_website}")
            target_hostname = self.domain_resolver.resolve(intent.target_website)
            target_pack = self.knowledge_service.get_pack(target_hostname)
            
            if target_pack:
                print(f"Using Cross-Site Planner for {hostname} -> {target_hostname}")
                delta = await self.cross_site_planner.plan(pack, target_pack, intent)
                impact_analysis = None
            else:
                print(f"Target Pack {target_hostname} not found. Falling back to Standard Planner.")
                if pack:
                    context = await self.graph_query_engine.query(intent, pack)
                else:
                    from ..knowledge.query import FilteredContext
                    context = FilteredContext(concepts=[])
                impact_analysis = await self.impact_analyzer.analyze(intent, context)
                delta = await self.transformation_planner.plan(impact_analysis)
        else:
            if pack:
                context = await self.graph_query_engine.query(intent, pack)
            else:
                from ..knowledge.query import FilteredContext
                context = FilteredContext(concepts=[])
                
            impact_analysis = await self.impact_analyzer.analyze(intent, context)
            delta = await self.transformation_planner.plan(impact_analysis)
        
        # Trace
        trace = PipelineTrace(
            intent=intent,
            impact_analysis=impact_analysis,
            transformation_delta=delta
        )
        
        # 10.4 Engineer
        preview = await self.css_js_engineer.generate_preview(prompt, delta, pack)
        
        # Apply the transformation directly
        await self.transform_executor.apply_css(preview.transformation_id, preview.transformation.css)
        await self.transform_executor.apply_javascript(preview.transformation_id, preview.transformation.javascript)
        
        # Save to registry for persistence
        if hasattr(self.browser, "transformation_manager"):
            from ..transform.models import SavedTransformation
            self.browser.transformation_manager.save_transformation(SavedTransformation(
                id=preview.transformation_id,
                hostname=hostname,
                css=preview.transformation.css,
                javascript=preview.transformation.javascript,
                enabled=True
            ))
        
        # The frontend expects a specific TransformExecutionResult
        execution = TransformExecutionResult(
            transformation_id=preview.transformation_id,
            success=True,
            applied_css=True,
            applied_javascript=True,
            message="Phase 10 executed successfully.",
            before_screenshot_path="",
            after_screenshot_path="",
            objective_metrics={},
            diff_summary="Applied operations: " + ", ".join([op.operation for op in delta.operations])
        )
        
        return TransformTestResponse(
            preview=preview,
            execution=execution,
            trace=trace
        )
