from pydantic import BaseModel
from typing import List

class RepairAttempt(BaseModel):
    feature_id: str
    old_selector: str
    new_selector: str
    success: bool
    confidence: float
    reason: str
    repair_method: str

class RepairResult(BaseModel):
    repaired_count: int
    failed_count: int
    attempts: List[RepairAttempt]
