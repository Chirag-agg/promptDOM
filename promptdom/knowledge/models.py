from pydantic import BaseModel, Field
from typing import Any, Optional


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


class PageVariantKnowledge(BaseModel):
    variant: str
    concepts: list[str]
    regions: list[str]
    frequency: float


class VisualSignature(BaseModel):
    theme: str = Field(description="e.g. 'dark', 'light', 'mixed'")
    navigation: str = Field(description="e.g. 'top', 'sidebar', 'bottom'")
    content_layout: str = Field(description="e.g. 'grid', 'horizontal_rows', 'masonry'")
    card_style: str = Field(description="e.g. 'compact', 'large_cinematic', 'minimal'")
    density: str = Field(description="e.g. 'low', 'medium', 'high'")


class KnowledgePack(BaseModel):
    pack_id: str

    hostname: str
    archetype: str
    patterns: list[str]
    visual_signature: Optional[VisualSignature] = None

    region_knowledge: list[RegionKnowledge]
    concept_knowledge: list[ConceptKnowledge]

    page_variants: list[PageVariantKnowledge]
    snapshots_used: list[str]

    graph: Any | None = None

    knowledge_confidence: float
    generated_at: str
