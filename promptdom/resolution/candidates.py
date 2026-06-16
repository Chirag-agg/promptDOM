from typing import List
from ..inspection.models import ResolutionInspectionResponse
from .models import ResolutionCandidate

class CandidateBuilder:
    def build(self, inspection: ResolutionInspectionResponse) -> List[ResolutionCandidate]:
        candidates = []
        
        def get_selector(el, default_tag: str) -> str:
            if getattr(el, 'id', None):
                return f"#{el.id}"
            if getattr(el, 'data_testid', None):
                return f'[data-testid="{el.data_testid}"]'
            if getattr(el, 'aria_label', None):
                # Escape quotes if necessary, but assume simple for now
                return f'[aria-label="{el.aria_label}"]'
            if getattr(el, 'css_path', None):
                return el.css_path
                
            selector = default_tag
            classes = getattr(el, 'classes', '')
            if classes:
                selector += f".{classes.split()[0]}"
            return selector

        for h in inspection.headings:
            candidates.append(ResolutionCandidate(
                id=h.id,
                target_type="heading",
                text=h.text,
                selector=get_selector(h, f"h{h.level}")
            ))
            
        for b in inspection.buttons:
            candidates.append(ResolutionCandidate(
                id=b.id,
                target_type="button",
                text=b.text,
                selector=get_selector(b, b.tag)
            ))
            
        for l in inspection.links:
            candidates.append(ResolutionCandidate(
                id=l.id,
                target_type="link",
                text=l.text,
                selector=get_selector(l, "a")
            ))
            
        for i in inspection.inputs:
            candidates.append(ResolutionCandidate(
                id=i.id,
                target_type="input",
                text=i.placeholder or i.name or i.type,
                selector=get_selector(i, i.type if i.type in ["textarea", "select"] else "input")
            ))
            
        for s in inspection.sections:
            candidates.append(ResolutionCandidate(
                id=s.id,
                target_type="section",
                text=s.text_preview or s.identifier,
                selector=get_selector(s, s.tag if s.tag else s.role)
            ))

        return candidates
