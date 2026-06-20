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
from ..design.models import DesignPlan

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
        design_planner: DesignPlanner,
        history_service=None
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
        self.history_service = history_service
        self.max_iterations = 3
        self.min_improvement = 0.05

    async def generate_plan(self, prompt: str) -> DesignPlan:
        # Capture Initial State
        initial_visual = await self.visual_service.capture_context()
        
        # Step 2: Design
        design_plan = await self.design_planner.generate_plan(prompt, initial_visual)
        return design_plan

    async def apply_redesign(self, prompt: str, design_plan: DesignPlan) -> TransformTestResponse:
        # Step 1: Goal Analysis
        goal = await self.goal_analyzer.analyze(prompt)
        
        # Capture Initial State again
        initial_visual = await self.visual_service.capture_context()
        initial_dom = await self.inspection_service.inspect_compact()
        
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
            if patch.js_patch and patch.js_patch.strip():
                current_js += f"\n/* Patch Iteration {i} */\n{{\n{patch.js_patch}\n}}"
            
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
            
        # Determine status
        status = "FAILED"
        if records and records[-1].success:
            status = "SUCCESS"
        elif last_confidence > 0.4:
            status = "PARTIAL"
            
        # Update preview with final aggregated code
        preview.transformation.css = current_css
        preview.transformation.javascript = current_js
        
        # We need final dom state for objective metrics
        final_dom = await self.inspection_service.inspect_compact()

        # Calculate dummy metrics for now or do actual count
        objective_metrics = {
            "dom_nodes_removed": len(initial_dom.sections) - len(final_dom.sections),
            "dom_nodes_added": len(final_dom.sections) - len(initial_dom.sections) if len(final_dom.sections) > len(initial_dom.sections) else 0,
            "dom_nodes_changed": len(preview.transformation.affected_elements)
        }
        
        # Final evaluation fallback
        final_feedback = records[-1].feedback if records else "No evaluation generated."

        # Save to history if history service is available
        from ..history.models import TransformationHistoryRecord
        import uuid
        
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        
        if hasattr(self, 'history_service') and self.history_service:
            record = TransformationHistoryRecord(
                run_id=run_id,
                prompt=prompt,
                site=initial_visual.page_context.url,
                status=status,
                reference_id=None, # Passed down if available, not currently in orchestrator args
                design_plan=design_plan,
                css=current_css,
                javascript=current_js,
                before_screenshot_path=initial_visual.visual_context.screenshot_path,
                after_screenshot_path=new_visual.visual_context.screenshot_path if 'new_visual' in locals() else initial_visual.visual_context.screenshot_path,
                objective_metrics=objective_metrics,
                iterations=records,
                diff_summary=final_feedback
            )
            self.history_service.save_record(record)
            
            before_screenshot_path = record.before_screenshot_path
            after_screenshot_path = record.after_screenshot_path
            reference_screenshot_path = record.reference_screenshot_path
        else:
            before_screenshot_path = initial_visual.visual_context.screenshot_path
            after_screenshot_path = new_visual.visual_context.screenshot_path if 'new_visual' in locals() else initial_visual.visual_context.screenshot_path
            reference_screenshot_path = None
        
        execution = TransformExecutionResult(
            transformation_id=preview.transformation_id,
            success=status == "SUCCESS",
            applied_css=True,
            applied_javascript=True,
            message=f"Redesign completed after {len(records)} iterations. Status: {status}",
            before_screenshot_path=f"/data/history/{run_id}/before.png" if self.history_service else f"/{before_screenshot_path}",
            after_screenshot_path=f"/data/history/{run_id}/after.png" if self.history_service else f"/{after_screenshot_path}",
            reference_screenshot_path=f"/data/history/{run_id}/reference.png" if self.history_service and reference_screenshot_path else None,
            objective_metrics=objective_metrics,
            diff_summary=final_feedback
        )
        
        return TransformTestResponse(
            preview=preview,
            execution=execution
        )
