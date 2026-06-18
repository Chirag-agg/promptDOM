import uuid
from typing import Dict, Any, Optional
from .models import GeneratedTransformation, TransformationPreviewResponse
from ..llm.base import BaseLLMProvider
from ..inspection.service import InspectionService
from ..design.models import DesignPlan

class ExperimentalTransformationService:
    def __init__(self, provider: BaseLLMProvider, inspection_service: InspectionService):
        self.provider = provider
        self.inspection_service = inspection_service
        self._previews: Dict[str, TransformationPreviewResponse] = {}

    async def generate_transformation(self, prompt: str, design_plan: DesignPlan, visual_context: Optional[Any] = None) -> GeneratedTransformation:
        # Step 1: Inspect the page to get context
        inspection_data = await self.inspection_service.inspect()
        
        # Step 2: Build the prompt
        system_prompt = (
            "You are a senior front-end engineer. "
            "Goal: Implement the provided DesignPlan using CSS and Javascript. "
            "IMPORTANT RULES:\n"
            "1. When writing CSS, ALWAYS use `!important` on every rule to ensure it overrides existing styles.\n"
            "2. When writing Javascript, ALWAYS check if elements exist (e.g. `if (el) ...`) before modifying them to prevent null reference errors.\n"
            "3. DO NOT invent your own redesign strategy. Follow the DesignPlan exactly.\n"
            "Return JSON only matching the exact schema."
        )
        
        # Format the context
        context_str = f"Page URL: {inspection_data.url}\n"
        context_str += f"Page Title: {inspection_data.title}\n\n"
        context_str += "Sections:\n"
        for section in inspection_data.sections[:10]: # Limit to avoid token overflow
            context_str += f"- {section.tag} (ID: {section.id}, Classes: {section.classes})\n"
        
        context_str += "\nButtons:\n"
        for btn in inspection_data.buttons[:10]:
            context_str += f"- Text: {btn.text} (ID: {btn.id}, Classes: {btn.classes})\n"
            
        context_str += "\nVisible Text Sample:\n"
        context_str += f"{inspection_data.visible_text_sample[:500]}...\n"
            
        full_prompt = (
            f"User Request: {prompt}\n\n"
            f"--- Design Plan Blueprint ---\n"
            f"{design_plan.model_dump_json(indent=2)}\n\n"
            f"--- Current Page Context ---\n"
            f"{context_str}\n"
            f"----------------------------\n\n"
            "Generate the CSS and Javascript to apply this transformation. "
            "Also provide reasoning, confidence, affected elements, and the transformation type."
        )

        # Step 3: LLM Call
        result = await self.provider.generate_structured(
            prompt=full_prompt,
            schema=GeneratedTransformation,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=4000
        )
        
        return result

    async def generate_preview(self, prompt: str, design_plan: DesignPlan, visual_context: Optional[Any] = None) -> TransformationPreviewResponse:
        transformation = await self.generate_transformation(prompt, design_plan, visual_context)
        
        # Generate UI Diff Summary
        diff_prompt = (
            f"User requested: {prompt}\n"
            f"We generated a transformation affecting elements: {', '.join(transformation.affected_elements)}\n"
            f"Reasoning: {transformation.reasoning}\n\n"
            "Please generate a clean, bulleted summary of the UI changes that will occur (e.g. 'Will hide: Shorts\\nWill move: Transcript')."
        )
        
        llm_response = await self.provider.generate(
            prompt=diff_prompt,
            system_prompt="You are a UI reviewer. Output only the short bulleted summary.",
            temperature=0.0
        )
        
        preview_id = str(uuid.uuid4())
        
        preview = TransformationPreviewResponse(
            transformation_id=preview_id,
            prompt=prompt,
            design_plan=design_plan,
            transformation=transformation,
            ui_diff_summary=llm_response.content
        )
        
        self._previews[preview_id] = preview
        return preview

    def get_preview(self, transformation_id: str) -> Optional[TransformationPreviewResponse]:
        return self._previews.get(transformation_id)

    async def generate_patch(
        self,
        prompt: str,
        design_plan: DesignPlan,
        feedback: str,
        candidates: dict,
        current_css: str,
        current_js: str
    ):
        from ..redesign.models import TransformationPatch
        system_prompt = (
            "You are a senior front-end engineer fixing a failed UI redesign.\n"
            "Your previous attempt failed. You will receive evaluator feedback and GROUNDED DOM SELECTORS.\n"
            "You must generate ONLY the CSS/JS patch required to fix the issue using the provided selectors.\n"
            "DO NOT regenerate the entire file. Generate only the new rules to append/override.\n"
            "Return JSON matching the schema."
        )
        
        candidates_str = ""
        for target, cands in candidates.items():
            candidates_str += f"- Target: {target}\n"
            for c in cands:
                candidates_str += f"  Candidate Selector: {c.selector} (Confidence: {c.confidence})\n"
                
        user_prompt = (
            f"Original Prompt: {prompt}\n\n"
            f"--- Failure Feedback ---\n{feedback}\n\n"
            f"--- Grounded DOM Selectors Found ---\n"
            f"{candidates_str}\n\n"
            f"--- Current CSS ---\n{current_css}\n\n"
            f"Generate a patch to fix the issue."
        )
        
        return await self.provider.generate_structured(
            prompt=user_prompt,
            schema=TransformationPatch,
            system_prompt=system_prompt,
            temperature=0.2,
            max_tokens=2000
        )
