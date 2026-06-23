import uuid
from typing import Dict, Any, Optional
from .models import GeneratedTransformation, TransformationPreviewResponse
from ..llm.base import BaseLLMProvider
from ..inspection.service import InspectionService
from ..intent.models import TransformationDelta
from ..knowledge.models import KnowledgePack

class CSSJSEngineerService:
    def __init__(self, provider: BaseLLMProvider, inspection_service: InspectionService):
        self.provider = provider
        self.inspection_service = inspection_service
        self._previews: Dict[str, TransformationPreviewResponse] = {}

    async def generate_preview(self, prompt: str, delta: TransformationDelta, pack: KnowledgePack) -> TransformationPreviewResponse:
        transformation = await self.generate_transformation(prompt, delta, pack)
        
        # We skip diff generation for preview performance, or do a simple stub
        preview = TransformationPreviewResponse(
            transformation_id=f"tx_{uuid.uuid4().hex[:8]}",
            transformation=transformation,
            ui_diff_summary="Generated from structural delta."
        )
        self._previews[preview.transformation_id] = preview
        return preview

    async def generate_transformation(self, prompt: str, delta: TransformationDelta, pack: KnowledgePack) -> GeneratedTransformation:
        inspection_data = await self.inspection_service.inspect_compact()
        
        system_prompt = (
            "You are a senior front-end engineer. "
            "Goal: Implement the requested Transformation Operations using CSS and Javascript. "
            "IMPORTANT RULES:\n"
            "1. Use ONLY the exact CSS selectors provided. Never invent selectors.\n"
            "2. NEVER use body, html, *, or any global reset rules.\n"
            "3. If a selector is marked NOT IN KNOWLEDGE PACK, use the DOM Candidates provided.\n"
            "4. If no valid selectors exist for a target, SKIP that operation entirely.\n"
            "5. Use `!important` on every rule to ensure it overrides existing styles.\n"
            "6. Check element existence before JS modifications.\n"
            "Return JSON only matching the exact schema."
        )
        
        def _match_concept(concept: str, target: str) -> bool:
            c, t = concept.lower(), target.lower()
            return c == t or c in t or t in c or any(
                word in t for word in c.split() if len(word) > 3
            )

        # Resolve selectors from Knowledge Pack
        resolved_targets = ""
        for op in delta.operations:
            selectors = []
            if pack:
                for ck in pack.concept_knowledge:
                    if _match_concept(ck.concept, op.target):
                        selectors = ck.selectors
                        break
            
            if not selectors:
                dom_candidates = [
                    s.id or " ".join(s.classes)
                    for s in inspection_data.sections
                    if op.target.lower() in (s.id or "").lower()
                    or any(op.target.lower() in c.lower() for c in s.classes)
                ]
                resolved_targets += (
                    f"- Operation: {op.operation}\n"
                    f"  Target Concept: {op.target}\n"
                    f"  Reason: {op.reason}\n"
                    f"  Known CSS Selectors: NOT IN KNOWLEDGE PACK\n"
                    f"  DOM Candidates (use these as starting point): {', '.join(dom_candidates[:5]) if dom_candidates else 'none found'}\n\n"
                )
            else:
                resolved_targets += (
                    f"- Operation: {op.operation}\n"
                    f"  Target Concept: {op.target}\n"
                    f"  Reason: {op.reason}\n"
                    f"  Known CSS Selectors: {', '.join(selectors)}\n\n"
                )

        context_str = f"Page URL: {inspection_data.url}\n"
        context_str += f"Page Title: {inspection_data.title}\n\n"
        context_str += "Sections (For context):\n"
        for section in inspection_data.sections[:200]:
            context_str += f"- {section.tag} (ID: {section.id}, Classes: {section.classes})\n"
            
        full_prompt = (
            f"User Original Request: {prompt}\n\n"
            f"--- Transformation Operations to Implement ---\n"
            f"{resolved_targets}\n"
            f"--- Current Page DOM Context ---\n"
            f"{context_str}\n"
            f"----------------------------\n\n"
            "Generate the CSS and Javascript to execute these operations. "
        )

        import os
        os.makedirs("scratch", exist_ok=True)
        with open("scratch/inspection_data.txt", "w", encoding="utf-8") as f:
            f.write(context_str)
        with open("scratch/resolved_targets.txt", "w", encoding="utf-8") as f:
            f.write(resolved_targets)

        result = await self.provider.generate_structured(
            prompt=full_prompt,
            schema=GeneratedTransformation,
            system_prompt=system_prompt,
            temperature=0.1,
            max_tokens=4000
        )
        
        return result
