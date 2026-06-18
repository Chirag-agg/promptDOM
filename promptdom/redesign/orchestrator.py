from typing import Optional
from ..browser import BrowserManager
from ..inspection.service import InspectionService
from ..visual.service import VisualInspectionService
from ..transform.service import ExperimentalTransformationService
from ..transform.executor import TransformExecutor
from ..transform.models import TransformTestResponse, TransformExecutionResult
from .goal_analyzer import GoalAnalyzerService
from .evaluator import EvaluatorService
from .repair import RedesignRepairService
from .models import IterationContext, IterationRecord, GoalAnalysis

from ..design.service import DesignPlanner

class RedesignOrchestrator:
    def __init__(
        self,
        browser: BrowserManager,
        inspection_service: InspectionService,
        visual_service: VisualInspectionService,
        transform_service: ExperimentalTransformationService,
        transform_executor: TransformExecutor,
        goal_analyzer: GoalAnalyzerService,
        evaluator: EvaluatorService,
        repair_service: RedesignRepairService,
        design_planner: DesignPlanner
    ):
        self.browser = browser
        self.inspection_service = inspection_service
        self.visual_service = visual_service
        self.transform_service = transform_service
        self.transform_executor = transform_executor
        self.goal_analyzer = goal_analyzer
        self.evaluator = evaluator
        self.repair_service = repair_service
        self.design_planner = design_planner
        self.max_iterations = 3
        self.min_improvement = 0.05

    async def execute_redesign_loop(self, prompt: str) -> TransformTestResponse:
        # Step 1: Goal Analysis
        goal = await self.goal_analyzer.analyze(prompt)
        
        # Capture Initial State
        initial_visual = await self.visual_service.capture_context()
        dom_snapshot = await self.inspection_service.inspect_compact()
        
        # Step 2: Design
        design_plan = await self.design_planner.generate_plan(prompt, initial_visual)
        
        # Step 3: Initial Transformation
        preview = await self.transform_service.generate_preview(prompt, design_plan, initial_visual)
        
        # Iteration Loop
        records = []
        current_css = preview.transformation.css
        current_js = preview.transformation.javascript
        last_confidence = 0.0
        
        for i in range(1, self.max_iterations + 1):
            # Apply current state
            await self.transform_executor.apply_css(preview.transformation_id, current_css)
            await self.transform_executor.apply_javascript(preview.transformation_id, current_js)
            
            # Capture New State
            new_visual = await self.visual_service.capture_context()
            
            # Evaluate
            evaluation = await self.evaluator.evaluate(
                prompt=prompt,
                goal=goal,
                before_screenshot_path=initial_visual.visual_context.screenshot_path,
                after_screenshot_path=new_visual.visual_context.screenshot_path
            )
            
            if evaluation.worked:
                # Success!
                records.append(IterationRecord(
                    iteration=i,
                    feedback=evaluation.feedback,
                    selectors_found=[],
                    patch_generated="",
                    success=True
                ))
                break
                
            # Check improvement threshold
            if i > 1 and (evaluation.confidence - last_confidence) < self.min_improvement:
                # Diminishing returns, abort loop
                break
                
            last_confidence = evaluation.confidence
            
            # Repair
            grounded_candidates = await self.repair_service.repair_targets(evaluation.unresolved_targets)
            
            # Generate Patch
            patch = await self.transform_service.generate_patch(
                prompt=prompt,
                design_plan=design_plan,
                feedback=evaluation.feedback,
                candidates=grounded_candidates,
                current_css=current_css,
                current_js=current_js
            )
            
            # Append Patch
            current_css += f"\n/* Patch Iteration {i} */\n{patch.css_patch}"
            current_js += f"\n/* Patch Iteration {i} */\n{patch.js_patch}"
            
            selectors_found = []
            for target, cands in grounded_candidates.items():
                if cands:
                    selectors_found.append(cands[0].selector)
                    
            records.append(IterationRecord(
                iteration=i,
                feedback=evaluation.feedback,
                selectors_found=selectors_found,
                patch_generated=patch.css_patch,
                success=False
            ))
            
        # Update preview with final aggregated code
        preview.transformation.css = current_css
        preview.transformation.javascript = current_js
        
        execution = TransformExecutionResult(
            transformation_id=preview.transformation_id,
            success=True,
            applied_css=True,
            applied_javascript=True,
            message=f"Redesign completed after {len(records)} iterations."
        )
        
        return TransformTestResponse(
            preview=preview,
            execution=execution
        )
