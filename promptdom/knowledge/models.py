from pydantic import BaseModel


class Bounds(BaseModel):
    x: float
    y: float
    width: float
    height: float


class RegionKnowledge(BaseModel):
    region_type: str
    common_selectors: list[str]
    avg_bounds: Bounds
    frequency: float
    confidence: float


class ConceptKnowledge(BaseModel):
    concept: str
    selectors: list[str]
    semantic_signals: list[str]
    region_types: list[str]
    frequency: float


class KnowledgePack(BaseModel):
    pack_id: str

    hostname: str
    archetype: str
    patterns: list[str]

    region_knowledge: list[RegionKnowledge]
    concept_knowledge: list[ConceptKnowledge]

    page_variants: list[str]
    snapshots_used: list[str]

    knowledge_confidence: float
    generated_at: str
