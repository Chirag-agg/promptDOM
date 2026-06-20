from typing import Optional
from .models import DesignPlan
from ..llm.base import BaseLLMProvider
from ..visual.models import VisualInspectionResponse
import base64

class DesignPlanner:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider

    async def generate_plan(
        self,
        prompt: str,
        inspection_context: VisualInspectionResponse
    ) -> DesignPlan:
        
        system_prompt = (
            "You are a senior product designer and UX architect.\n"
            "Do NOT generate CSS.\n"
            "Do NOT generate JavaScript.\n"
            "Use BOTH:\n"
            "1. Structured DOM summary\n"
            "2. Screenshot\n\n"
            "The screenshot is the primary source for layout and visual hierarchy.\n"
            "The DOM summary is the primary source for element identification.\n"
            "Analyze the website structure and create a high-level redesign strategy blueprint.\n"
            "IMPORTANT: While you must provide the layout, content, and visual strategies, you MUST ALSO explicitly break down the redesign into an actionable `changes` array consisting of typed structural instructions (REMOVE, MOVE, RESTYLE, ADD)."
            "Return ONLY a DesignPlan."
        )
        
        page_context = inspection_context.page_context
        
        # Format the context
        context_str = f"Page URL: {page_context.url}\n"
        context_str += f"Page Title: {page_context.title}\n\n"
        context_str += "Sections:\n"
        for section in page_context.sections[:10]: # Limit to avoid token overflow
            context_str += f"- {section.tag} (ID: {section.id}, Classes: {section.classes})\n"
        
        context_str += "\nButtons:\n"
        for btn in page_context.buttons[:10]:
            context_str += f"- Text: {btn.text} (ID: {btn.id}, Classes: {btn.classes})\n"
            
        context_str += "\nVisible Text Sample:\n"
        context_str += f"{page_context.visible_text_sample[:500]}...\n"
            
        full_prompt = (
            f"User Redesign Request: {prompt}\n\n"
            f"--- Current Page Context ---\n"
            f"{context_str}\n"
            f"----------------------------\n\n"
            "Create a DesignPlan to fulfill the User Redesign Request based on the Current Page Context and Screenshot."
        )

        capabilities = self.provider.capabilities
        if capabilities.supports_vision:
            with open(inspection_context.visual_context.screenshot_path, "rb") as f:
                img_base64 = base64.b64encode(f.read()).decode("utf-8")
            
            initial_plan = await self.provider.generate_multimodal_structured(
                prompt=full_prompt,
                images_base64=[img_base64],
                schema=DesignPlan,
                system_prompt=system_prompt,
                temperature=0.2
            )
        else:
            initial_plan = await self.provider.generate_structured(
                prompt=full_prompt,
                schema=DesignPlan,
                system_prompt=system_prompt,
                temperature=0.2
            )
        
        return await self.critique_plan(initial_plan)

    async def critique_plan(self, plan: DesignPlan) -> DesignPlan:
        system_prompt = (
            "You are a Principal UX Architect reviewing a junior designer's blueprint.\n"
            "Do NOT generate CSS.\n"
            "Do NOT generate JavaScript.\n"
            "Review the design plan. Identify missing layout decisions, contradictions, or unrealistic transformations.\n"
            "Return an improved, corrected DesignPlan."
        )
        
        full_prompt = (
            f"Please review and improve the following DesignPlan:\n\n"
            f"{plan.model_dump_json(indent=2)}\n\n"
            "Output the final improved DesignPlan."
        )
        
        improved_plan = await self.provider.generate_structured(
            prompt=full_prompt,
            schema=DesignPlan,
            system_prompt=system_prompt,
            temperature=0.1
        )
        
        return improved_plan
