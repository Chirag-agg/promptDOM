import uuid
import urllib.parse
from datetime import datetime, timezone
from collections import defaultdict, Counter
import re

from promptdom.capture.storage import CaptureStorage
from promptdom.intelligence.service import IntelligenceService
from promptdom.archetypes.service import ArchetypeService
from promptdom.archetypes.models import WebsiteArchetype
from promptdom.knowledge_graph.builder import GraphBuilder
from .models import KnowledgePack, RegionKnowledge, ConceptKnowledge, Bounds, PageVariantKnowledge


class KnowledgeBuilder:
    def __init__(
        self,
        capture_storage: CaptureStorage,
        intelligence_service: IntelligenceService,
        archetype_service: ArchetypeService
    ):
        self.capture_storage = capture_storage
        self.intelligence_service = intelligence_service
        self.archetype_service = archetype_service

    def build(self, hostname: str) -> KnowledgePack | None:
        # 1. Fetch all snapshots
        all_snapshots = self.capture_storage.list_snapshots()
        snapshots = [s for s in all_snapshots if s.hostname == hostname or hostname in s.url]
        
        if not snapshots:
            return None

        snapshot_ids = [s.snapshot_id for s in snapshots]
        total_snaps = len(snapshots)

        # 2. Extract variant groups
        variant_snapshots = defaultdict(list)
        for s in snapshots:
            parsed = urllib.parse.urlparse(s.url)
            path = parsed.path
            if not path or path == "/":
                v_name = "home"
            else:
                v_name = path.strip("/").split("/")[0]
            variant_snapshots[v_name].append(s)

        # 3. Analyze all
        archetype_counts = Counter()
        pattern_counts = Counter()
        
        region_instances = defaultdict(list)
        concept_instances = defaultdict(list)

        for s in snapshots:
            web_model = self.intelligence_service.analyze(s, force=False)
            arc_result = self.archetype_service.detect(s, web_model)
            
            archetype_counts[arc_result.archetype] += 1
            for p in arc_result.patterns:
                pattern_counts[p] += 1
                
            for r in web_model.regions:
                region_instances[r.region_type].append(r)
                
            # Mine semantic concepts
            for sem in s.semantic_elements:
                text_val = (sem.aria_label or sem.text or "").strip().lower()
                
                # Noise reduction heuristics
                if len(text_val) <= 2 or len(text_val) >= 20:
                    continue
                if re.search(r'\d', text_val):  # Ignore strings with numbers (times, views, dates)
                    continue
                if not re.search(r'[a-z]', text_val):  # Must contain letters
                    continue
                    
                noise_words = {'views', 'ago', 'subscribers', 'likes', 'dislikes', 'months', 'years', 'days', 'hours'}
                if set(text_val.split()).intersection(noise_words):
                    continue
                    
                concept_instances[text_val].append((sem.selector, "UNKNOWN"))

        # Archetype & Patterns
        best_archetype = archetype_counts.most_common(1)[0][0] if archetype_counts else WebsiteArchetype.UNKNOWN
        final_patterns = [p for p, count in pattern_counts.items() if count / total_snaps >= 0.4]

        # Aggregated RegionKnowledge
        region_knowledge = []
        for r_type, instances in region_instances.items():
            freq = len(instances) / total_snaps
            if freq >= 0.3:
                avg_x = sum(i.x for i in instances) / len(instances)
                avg_y = sum(i.y for i in instances) / len(instances)
                avg_w = sum(i.width for i in instances) / len(instances)
                avg_h = sum(i.height for i in instances) / len(instances)
                avg_conf = sum(i.confidence for i in instances) / len(instances)
                
                sel_counts = Counter(i.selector for i in instances)
                common_sels = [s for s, c in sel_counts.most_common(3)]
                
                region_knowledge.append(RegionKnowledge(
                    region_type=r_type,
                    common_selectors=common_sels,
                    avg_bounds=Bounds(x=avg_x, y=avg_y, width=avg_w, height=avg_h),
                    frequency=round(freq, 2),
                    confidence=round(avg_conf, 2)
                ))

        # Aggregated ConceptKnowledge
        concept_knowledge = []
        for concept_str, instances in concept_instances.items():
            freq = len(instances) / total_snaps
            if freq > 0.5:
                sel_counts = Counter(sel for sel, rtype in instances)
                common_sels = [s for s, c in sel_counts.most_common(3)]
                
                r_types = set()
                for sel in common_sels:
                    for rk in region_knowledge:
                        if sel in rk.common_selectors or any(sel.startswith(rs) for rs in rk.common_selectors):
                            r_types.add(rk.region_type)
                
                if not r_types:
                    r_types.add("MAIN_CONTENT")
                
                concept_knowledge.append(ConceptKnowledge(
                    concept=concept_str,
                    selectors=common_sels,
                    semantic_signals=[concept_str],
                    region_types=list(r_types),
                    frequency=round(freq, 2)
                ))

        concept_knowledge.sort(key=lambda x: x.frequency, reverse=True)
        concept_knowledge = concept_knowledge[:20]

        # Page Variants Knowledge
        page_variants = []
        for v_name, v_snaps in variant_snapshots.items():
            v_concepts = []
            v_regions = []
            v_freq = len(v_snaps) / total_snaps
            
            # which concepts are in these snaps?
            for ck in concept_knowledge:
                c_matches = sum(1 for sel, rtype in concept_instances[ck.concept] if any(s.snapshot_id in str(concept_instances[ck.concept]) for s in v_snaps))
                # simple approximation: if the concept appeared in at least 30% of this variant's snapshots
                # Actually, a better way is to just assume if it's a global concept, does it ever appear in this variant?
                c_matches = 0
                for s in v_snaps:
                    if any((sem.aria_label or sem.text or "").strip().lower() == ck.concept for sem in s.semantic_elements):
                        c_matches += 1
                if c_matches / len(v_snaps) >= 0.3:
                    v_concepts.append(ck.concept)

            # which regions are in these snaps?
            for rk in region_knowledge:
                r_matches = 0
                for s in v_snaps:
                    wm = self.intelligence_service.analyze(s)
                    if any(r.region_type == rk.region_type for r in wm.regions):
                        r_matches += 1
                if r_matches / len(v_snaps) >= 0.3:
                    v_regions.append(rk.region_type)
            
            page_variants.append(PageVariantKnowledge(
                variant=v_name,
                concepts=v_concepts,
                regions=v_regions,
                frequency=round(v_freq, 2)
            ))

        # Knowledge Confidence
        base_conf = min(1.0, total_snaps / 10.0)
        arc_stability = archetype_counts[best_archetype] / total_snaps if total_snaps > 0 else 0
        knowledge_confidence = round(base_conf * 0.7 + arc_stability * 0.3, 2)

        # Generate Graph
        graph = GraphBuilder.build(region_knowledge, concept_knowledge, page_variants)

        pack = KnowledgePack(
            pack_id=str(uuid.uuid4()),
            hostname=hostname,
            archetype=best_archetype,
            patterns=final_patterns,
            region_knowledge=region_knowledge,
            concept_knowledge=concept_knowledge,
            page_variants=page_variants,
            snapshots_used=snapshot_ids,
            graph=graph.model_dump() if graph else None,
            knowledge_confidence=knowledge_confidence,
            generated_at=datetime.now(timezone.utc).isoformat()
        )
        return pack
