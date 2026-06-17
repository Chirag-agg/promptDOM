import uuid
from typing import Dict, Any, Optional
from .models import GeneratedTransformation, TransformationPreviewResponse
from ..llm.base import BaseLLMProvider
from ..inspection.service import InspectionService

class ExperimentalTransformationService:
    def __init__(self, provider: BaseLLMProvider, inspection_service: InspectionService):
        self.provider = provider
        self.inspection_service = inspection_service
        self._previews: Dict[str, TransformationPreviewResponse] = {}

    async def generate_transformation(self, prompt: str, visual_context: Optional[Any] = None) -> GeneratedTransformation:
        # Step 1: Inspect the page to get context
        inspection_data = await self.inspection_service.inspect()
        
        # Step 2: Build the prompt
        system_prompt = (
            "You are a senior front-end engineer. "
            "Goal: Modify the current website according to the user's request. "
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
            temperature=0.2
        )
        
        return result

    async def generate_preview(self, prompt: str, visual_context: Optional[Any] = None) -> TransformationPreviewResponse:
        transformation = await self.generate_transformation(prompt, visual_context)
        
        # Generate UI Diff Summary
        diff_prompt = (
            f"User requested: {prompt}\n"
            f"We generated a transformation affecting elements: {', '.join(transformation.affected_elements)}\n"
            f"Reasoning: {transformation.reasoning}\n\n"
            "Please generate a clean, bulleted summary of the UI changes that will occur (e.g. 'Will hide: Shorts\\nWill move: Transcript')."
        )
        
        diff_summary_response = await self.provider.generate_text(
            prompt=diff_prompt,
            system_prompt="You are a UI reviewer. Output only the short bulleted summary.",
            temperature=0.0
        )
        
        preview_id = str(uuid.uuid4())
        
        preview = TransformationPreviewResponse(
            transformation_id=preview_id,
            transformation=transformation,
            ui_diff_summary=diff_summary_response
        )
        
        self._previews[preview_id] = preview
        return preview

    def get_preview(self, transformation_id: str) -> Optional[TransformationPreviewResponse]:
        return self._previews.get(transformation_id)
