from pydantic import BaseModel, Field
from typing import List, Literal, Optional

# Phase 10.0: Intent Interpreter
class DesignIntent(BaseModel):
    principles: List[str] = Field(description="High-level design principles to apply (e.g. 'reduce visual noise', 'increase focus on primary content')")
    target_website: Optional[str] = Field(default=None, description="The name of the target website to mimic, if the user asks to 'Make X like Y' (e.g., 'netflix', 'x', 'gmail'). Otherwise null.")


# Phase 10.2: Impact Analyzer
class ConceptImpact(BaseModel):
    concept: str = Field(description="The logical concept from the knowledge graph")
    effect: Literal["REMOVE", "DEEMPHASIZE", "EMPHASIZE", "PRIORITIZE", "REPOSITION", "GROUP"]
    reason: str = Field(description="Reason why this concept violates or supports the design principles")
    confidence: float = Field(description="Confidence in this assessment (0.0 to 1.0)")

class ImpactAnalysis(BaseModel):
    impacts: List[ConceptImpact] = Field(description="List of concepts and how they should be impacted")


# Phase 10.3: Transformation Planner
class TransformationOperation(BaseModel):
    operation: Literal["REMOVE", "COLLAPSE", "RESTYLE", "ADD", "PRIORITIZE"]
    target: str = Field(description="The target logical concept (e.g., 'Shorts')")
    reason: str = Field(description="Reason for this specific operation")
    priority: int = Field(description="Execution priority (1 is highest)")

class TransformationDelta(BaseModel):
    operations: List[TransformationOperation] = Field(description="Concrete operations to perform on the concepts")


# Pipeline Trace for Debugging
class PipelineTrace(BaseModel):
    intent: Optional[DesignIntent] = None
    impact_analysis: Optional[ImpactAnalysis] = None
    transformation_delta: Optional[TransformationDelta] = None
