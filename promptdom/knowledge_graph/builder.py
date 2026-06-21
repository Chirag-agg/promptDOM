from .models import WebsiteGraph, KnowledgeTriple, KnowledgeRelation
from promptdom.knowledge.models import RegionKnowledge, ConceptKnowledge, PageVariantKnowledge

class GraphBuilder:
    @staticmethod
    def build(
        regions: list[RegionKnowledge], 
        concepts: list[ConceptKnowledge], 
        variants: list[PageVariantKnowledge]
    ) -> WebsiteGraph:
        triples = []
        
        # 1. VISIBLE_ON and PART_OF from variants
        for v in variants:
            for c in v.concepts:
                triples.append(KnowledgeTriple(source=c, relation=KnowledgeRelation.VISIBLE_ON, target=v.variant, confidence=v.frequency))
                triples.append(KnowledgeTriple(source=c, relation=KnowledgeRelation.PART_OF, target=f"{v.variant} page", confidence=v.frequency))
                
            for r in v.regions:
                triples.append(KnowledgeTriple(source=r, relation=KnowledgeRelation.VISIBLE_ON, target=v.variant, confidence=v.frequency))
                triples.append(KnowledgeTriple(source=r, relation=KnowledgeRelation.PART_OF, target=f"{v.variant} page", confidence=v.frequency))

        # 2. LOCATED_IN and CONTAINS from concepts
        for c in concepts:
            for r in c.region_types:
                triples.append(KnowledgeTriple(source=c.concept, relation=KnowledgeRelation.LOCATED_IN, target=r, confidence=c.frequency))
                triples.append(KnowledgeTriple(source=r, relation=KnowledgeRelation.CONTAINS, target=c.concept, confidence=c.frequency))

        # 3. ABOVE, BELOW, NEAR from region layout bounds
        for r1 in regions:
            for r2 in regions:
                if r1.region_type == r2.region_type:
                    continue
                
                conf = min(r1.frequency, r2.frequency)
                b1 = r1.avg_bounds
                b2 = r2.avg_bounds
                
                if b1.y + b1.height < b2.y + (b2.height * 0.1):
                    triples.append(KnowledgeTriple(source=r1.region_type, relation=KnowledgeRelation.ABOVE, target=r2.region_type, confidence=conf))
                    triples.append(KnowledgeTriple(source=r2.region_type, relation=KnowledgeRelation.BELOW, target=r1.region_type, confidence=conf))
                
                x_gap = max(0, max(b1.x - (b2.x + b2.width), b2.x - (b1.x + b1.width)))
                y_gap = max(0, max(b1.y - (b2.y + b2.height), b2.y - (b1.y + b1.height)))
                
                if x_gap < 100 and y_gap < 100:
                    triples.append(KnowledgeTriple(source=r1.region_type, relation=KnowledgeRelation.NEAR, target=r2.region_type, confidence=conf))
                    
        # Remove duplicates
        unique_triples = []
        seen = set()
        for t in triples:
            key = f"{t.source}|{t.relation.value}|{t.target}"
            if key not in seen:
                seen.add(key)
                unique_triples.append(t)
                
        # Sort by confidence
        unique_triples.sort(key=lambda x: x.confidence, reverse=True)

        return WebsiteGraph(triples=unique_triples)
