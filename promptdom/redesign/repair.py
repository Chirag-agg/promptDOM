from typing import List, Dict
from ..resolution.resolver import SemanticResolver
from .models import GroundedCandidate

class RedesignRepairService:
    def __init__(self, semantic_resolver: SemanticResolver):
        self.resolver = semantic_resolver

    async def repair_targets(self, targets: List[str]) -> Dict[str, List[GroundedCandidate]]:
        """
        Takes a list of logical targets (e.g. 'Shorts shelf') that failed to be removed/modified,
        and returns a ranked list of grounded DOM candidates for each target.
        """
        grounded_targets: Dict[str, List[GroundedCandidate]] = {}
        
        for target in targets:
            # We don't necessarily know the exact target_type here, so we default to "element"
            resolution = await self.resolver.resolve(target, "element")
            
            candidates = []
            # Map top_candidates to our GroundedCandidate model
            for c in resolution.top_candidates:
                candidates.append(GroundedCandidate(
                    selector=c.selector,
                    confidence=c.score,
                    reason=c.match_reason
                ))
                
            # If no top candidates but it matched via cache/registry, add it
            if not candidates and resolution.matched and resolution.selector:
                candidates.append(GroundedCandidate(
                    selector=resolution.selector,
                    confidence=resolution.confidence,
                    reason=resolution.explanation
                ))
                
            grounded_targets[target] = candidates
            
        return grounded_targets
