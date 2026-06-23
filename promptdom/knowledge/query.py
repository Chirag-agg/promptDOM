from pydantic import BaseModel, Field
from typing import List
from ..llm.base import BaseLLMProvider
from .models import KnowledgePack
from ..intent.models import DesignIntent

class FilteredContext(BaseModel):
    concepts: List[str] = Field(description="List of relevant concept names")

class GraphQueryEngine:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
        self.system_prompt = (
            "You are a graph query engine. "
            "Your job is to select the most relevant concepts from a site's Knowledge Graph that need to be evaluated based on the given design intent.\n"
            "Return JSON matching the requested schema."
        )

    async def query(self, intent: DesignIntent, pack: KnowledgePack) -> FilteredContext:
        all_concepts = [ck.concept for ck in pack.concept_knowledge]
        # If there are fewer than 20 concepts, just return them all
        if len(all_concepts) <= 20:
            return FilteredContext(concepts=all_concepts)
            
        user_prompt = (
            f"Design Intent Principles: {intent.principles}\n\n"
            f"Available Concepts in Knowledge Graph:\n"
            f"{', '.join(all_concepts)}\n\n"
            "Select up to 20 concepts that are most relevant to achieving the design intent."
        )
        
        return await self.provider.generate_structured(
            prompt=user_prompt,
            schema=FilteredContext,
            system_prompt=self.system_prompt,
            temperature=0.0
        )
