from pydantic import BaseModel, Field
from typing import List, Optional

class ResolutionCandidate(BaseModel):
    id: str = ""
    target_type: str
    text: str
    selector: str
    score: float = 0.0
    match_reason: str = ""

class ResolutionResult(BaseModel):
    matched: bool
    selector: str
    confidence: float
    explanation: str
    candidate_count: int
    top_candidates: List[ResolutionCandidate]
