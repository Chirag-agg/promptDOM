from ..llm.base import BaseLLMProvider
from ..knowledge.models import KnowledgePack
from ..intent.models import DesignIntent, TransformationDelta

class CrossSitePlannerService:
    def __init__(self, provider: BaseLLMProvider):
        self.provider = provider
        self.system_prompt = (
            "You are an expert UX/UI architect and website transformation engine. "
            "Your task is to compare a Source Knowledge Pack against a Target Knowledge Pack "
            "and generate a TransformationDelta that restructures the Source to look and feel like the Target. "
            "You must strictly compare Regions, Concepts, Relations, and Visual Signatures. "
            "Do not output raw CSS or HTML. Only output structural layout and design operations matching the schema."
        )

    async def plan(self, source_pack: KnowledgePack, target_pack: KnowledgePack, intent: DesignIntent) -> TransformationDelta:
        source_json = source_pack.model_dump_json(exclude={"graph", "snapshots_used"})
        target_json = target_pack.model_dump_json(exclude={"graph", "snapshots_used"})
        
        prompt = (
            f"User Intent Principles: {intent.principles}\n\n"
            f"=== SOURCE WEBSITE ({source_pack.hostname}) ===\n{source_json}\n\n"
            f"=== TARGET WEBSITE ({target_pack.hostname}) ===\n{target_json}\n\n"
            "Compare the structures. Produce a set of operations (REMOVE, ADD, RESTYLE, REORGANIZE) "
            "to transform the Source to match the Target. "
        )
        
        return await self.provider.generate_structured(
            prompt=prompt,
            schema=TransformationDelta,
            system_prompt=self.system_prompt,
            temperature=0.2
        )
