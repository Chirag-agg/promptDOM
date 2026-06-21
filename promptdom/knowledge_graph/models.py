from enum import Enum
from pydantic import BaseModel


class KnowledgeRelation(str, Enum):
    LOCATED_IN = "LOCATED_IN"
    CONTAINS = "CONTAINS"
    NEAR = "NEAR"
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    ADJACENT_TO = "ADJACENT_TO"
    VISIBLE_ON = "VISIBLE_ON"
    PART_OF = "PART_OF"


class KnowledgeTriple(BaseModel):
    source: str
    relation: KnowledgeRelation
    target: str
    confidence: float


class WebsiteGraph(BaseModel):
    triples: list[KnowledgeTriple]
