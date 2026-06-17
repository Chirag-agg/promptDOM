from typing import Set
from ..inspection.models import ResolutionInspectionResponse
from ..resolution.candidates import CandidateBuilder

class SelectorVerifier:
    def __init__(self, candidate_builder: CandidateBuilder):
        self.builder = candidate_builder

    def get_alive_selectors(self, inspection: ResolutionInspectionResponse) -> Set[str]:
        """
        Builds a set of all currently valid selectors on the page 
        using the deterministic CandidateBuilder.
        """
        candidates = self.builder.build(inspection)
        return {c.selector for c in candidates}
