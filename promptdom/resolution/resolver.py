from .models import ResolutionResult
from .candidates import CandidateBuilder
from .scorer import ScoringEngine
from .cache import ResolutionCache
from ..inspection.service import InspectionService

class SemanticResolver:
    def __init__(self, inspection_service: InspectionService):
        self.inspection_service = inspection_service
        self.candidate_builder = CandidateBuilder()
        self.scorer = ScoringEngine()
        self.cache = ResolutionCache()

        # Legacy feature registry fallback
        self.registry = {
            "youtube_shorts": "#shorts-container",
            "comments": "#comments",
            "sidebar": "#secondary"
        }

    async def resolve(self, target: str, target_type: str) -> ResolutionResult:
        inspection = await self.inspection_service.inspect_resolution()
        fingerprint = inspection.dom_fingerprint
        
        cached_selector = self.cache.get(fingerprint, target, target_type)
        if cached_selector:
            return ResolutionResult(
                matched=True,
                selector=cached_selector,
                confidence=1.0,
                explanation="Matched via cache",
                candidate_count=0,
                top_candidates=[]
            )
            
        if target in self.registry:
            selector = self.registry[target]
            return ResolutionResult(
                matched=True,
                selector=selector,
                confidence=1.0,
                explanation="Matched via legacy feature registry",
                candidate_count=0,
                top_candidates=[]
            )

        candidates = self.candidate_builder.build(inspection)
        
        scored_candidates = []
        for c in candidates:
            scored = self.scorer.score(target, target_type, c)
            if scored.score > 0:
                scored_candidates.append(scored)
                
        scored_candidates.sort(key=lambda x: x.score, reverse=True)
        top_candidates = scored_candidates[:5]
        
        if not top_candidates:
            return ResolutionResult(
                matched=False,
                selector="",
                confidence=0.0,
                explanation="No candidates matched the description",
                candidate_count=len(candidates),
                top_candidates=[]
            )
            
        best_match = top_candidates[0]
        confidence = best_match.score
        
        if confidence >= 0.8:
            matched = True
            explanation = f"High confidence match: {best_match.match_reason}"
            self.cache.set(fingerprint, target, target_type, best_match.selector)
        elif confidence >= 0.6:
            matched = True
            explanation = f"Warning: Low confidence match ({confidence:.2f}): {best_match.match_reason}"
        else:
            matched = False
            explanation = f"Ambiguous target: Best match was only {confidence:.2f} ({best_match.match_reason})"
            
        return ResolutionResult(
            matched=matched,
            selector=best_match.selector if matched else "",
            confidence=confidence,
            explanation=explanation,
            candidate_count=len(candidates),
            top_candidates=top_candidates
        )
