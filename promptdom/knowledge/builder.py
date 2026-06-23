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


STRUCTURAL_SIGNALS = {
    "shorts": {
        "selectors": ["ytd-reel-shelf-renderer", "#shorts-container"],
        "id_patterns": ["shorts", "reel"],
        "tag_patterns": ["ytd-reel-shelf-renderer"],
    },
    "sidebar": {
        "selectors": ["#secondary", "ytd-watch-next-secondary-results-renderer"],
        "id_patterns": ["secondary", "related"],
        "tag_patterns": ["ytd-watch-next-secondary-results-renderer"],
    },
    "feed": {
        "selectors": ["ytd-rich-grid-renderer", "#contents.ytd-rich-grid-renderer"],
        "id_patterns": ["contents", "feed"],
        "tag_patterns": ["ytd-rich-grid-renderer"],
    },
    "header": {
        "selectors": ["#masthead", "ytd-masthead"],
        "id_patterns": ["masthead", "header"],
        "tag_patterns": ["ytd-masthead"],
    },
    "guide": {
        "selectors": ["#guide", "ytd-guide-renderer", "ytd-mini-guide-renderer"],
        "id_patterns": ["guide"],
        "tag_patterns": ["ytd-guide-renderer", "ytd-mini-guide-renderer"],
    },
    "search": {
        "selectors": ["yt-searchbox", "#search-form"],
        "id_patterns": ["search"],
        "tag_patterns": ["yt-searchbox"],
    },
    "chips_bar": {
        "selectors": ["yt-chip-cloud-renderer", "#chips-wrapper"],
        "id_patterns": ["chips"],
        "tag_patterns": ["yt-chip-cloud-renderer"],
    },
    "video_player": {
        "selectors": ["ytd-watch-flexy", "#player", "video.html5-main-video"],
        "id_patterns": ["player", "movie_player"],
        "tag_patterns": ["ytd-watch-flexy"],
    },
    "comments": {
        "selectors": ["#comments", "ytd-comments"],
        "id_patterns": ["comments"],
        "tag_patterns": ["ytd-comments"],
    },
    "notifications": {
        "selectors": ["ytd-notification-topbar-button-renderer"],
        "id_patterns": ["notification"],
        "tag_patterns": ["ytd-notification-topbar-button-renderer"],
    },
}


class KnowledgeBuilder:
    def __init__(
        self,
        capture_storage: CaptureStorage,
        intelligence_service: IntelligenceService,
        archetype_service: ArchetypeService,
        provider=None
    ):
        self.capture_storage = capture_storage
        self.intelligence_service = intelligence_service
        self.archetype_service = archetype_service
        self.provider = provider

    def _extract_tags_and_ids(self, clean_dom: str) -> list[dict]:
        """Parse clean DOM HTML and extract tag name, id, and classes for each element."""
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(clean_dom, "html.parser")
        elements = []
        for el in soup.find_all(True):  # all tags
            elements.append({
                "tag": el.name,
                "id": el.get("id", ""),
                "classes": el.get("class", []),
            })
        return elements

    def _mine_structural_concepts(self, snapshots) -> list[ConceptKnowledge]:
        """
        Mine concepts from DOM structure, not text content.
        Uses tag names, IDs, and class patterns — never aria_label or text.
        """
        concept_hits = defaultdict(list)  # concept_name -> list of confirmed selectors

        for s in snapshots:
            try:
                with open(s.dom_path, "r", encoding="utf-8") as f:
                    clean_dom_content = f.read()
                dom_tags = self._extract_tags_and_ids(clean_dom_content)  # parse clean_dom for tags + ids
            except Exception as e:
                print(f"Failed to read DOM path {s.dom_path}: {e}")
                continue

            for concept_name, signals in STRUCTURAL_SIGNALS.items():
                matched_selectors = []

                for tag in dom_tags:
                    tag_name = tag.get("tag", "").lower()
                    tag_id = tag.get("id", "").lower()
                    tag_classes = " ".join(tag.get("classes", []) if isinstance(tag.get("classes"), list) else tag.get("classes", "").split()).lower()

                    # Match by custom element tag name
                    for tp in signals["tag_patterns"]:
                        if tag_name == tp.lower():
                            matched_selectors.append(tp)
                            break

                    # Match by ID pattern
                    for ip in signals["id_patterns"]:
                        if ip in tag_id:
                            matched_selectors.append(f"#{tag_id}")
                            break

                if matched_selectors:
                    # Add the known canonical selectors too
                    all_selectors = list(dict.fromkeys(
                        signals["selectors"] + matched_selectors
                    ))
                    concept_hits[concept_name].append(all_selectors)

        # Build ConceptKnowledge only for concepts found in >15% of snapshots
        result = []
        total = len(snapshots)
        for concept_name, selector_lists in concept_hits.items():
            freq = len(selector_lists) / total
            if freq < 0.15:
                continue

            # Flatten and deduplicate selectors, most common first
            all_sels = [s for sublist in selector_lists for s in sublist]
            sel_counts = Counter(all_sels)
            final_selectors = [s for s, _ in sel_counts.most_common(5)]

            result.append(ConceptKnowledge(
                concept=concept_name,
                selectors=final_selectors,
                semantic_signals=list(STRUCTURAL_SIGNALS[concept_name]["tag_patterns"]),
                region_types=["STRUCTURE"],
                frequency=round(freq, 2)
            ))

        return result

    async def build(self, hostname: str) -> KnowledgePack | None:
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

        # Aggregated ConceptKnowledge using structural layers
        concept_knowledge = self._mine_structural_concepts(snapshots)

        # Page Variants Knowledge
        page_variants = []
        for v_name, v_snaps in variant_snapshots.items():
            v_concepts = []
            v_regions = []
            v_freq = len(v_snaps) / total_snaps
            
            # which concepts are in these snaps?
            for ck in concept_knowledge:
                # Since structural concepts are global components, we'll just check if their selectors exist in the DOMs
                c_matches = 0
                for s in v_snaps:
                    try:
                        with open(s.dom_path, "r", encoding="utf-8") as f:
                            dom_content = f.read()
                        if any(sel.strip("#.") in dom_content for sel in ck.selectors):
                            c_matches += 1
                    except:
                        pass
                if len(v_snaps) > 0 and c_matches / len(v_snaps) >= 0.3:
                    v_concepts.append(ck.concept)

            # which regions are in these snaps?
            for rk in region_knowledge:
                r_matches = 0
                for s in v_snaps:
                    wm = self.intelligence_service.analyze(s)
                    if any(r.region_type == rk.region_type for r in wm.regions):
                        r_matches += 1
                if len(v_snaps) > 0 and r_matches / len(v_snaps) >= 0.3:
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

        # Visual Signature Extraction
        visual_signature = None
        if self.provider and snapshots:
            try:
                system_prompt = (
                    "You are an expert UX designer analyzing a website's visual signature. "
                    "Extract the overarching theme, navigation style, content layout, card style, and visual density. "
                    "Output JSON matching the schema."
                )
                from .models import VisualSignature
                if getattr(self.provider.capabilities, 'supports_vision', False) and snapshots[0].screenshot_path:
                    import base64
                    with open(snapshots[0].screenshot_path, "rb") as f:
                        img_b64 = base64.b64encode(f.read()).decode("utf-8")
                    visual_signature = await self.provider.generate_multimodal_structured(
                        prompt="Analyze this website's visual signature based on the provided screenshot.",
                        images_base64=[img_b64],
                        schema=VisualSignature,
                        system_prompt=system_prompt,
                        temperature=0.1
                    )
                else:
                    visual_signature = await self.provider.generate_structured(
                        prompt=f"Analyze the visual signature of {hostname} based on general knowledge.",
                        schema=VisualSignature,
                        system_prompt=system_prompt,
                        temperature=0.1
                    )
            except Exception as e:
                print(f"Failed to extract visual signature: {e}")

        pack = KnowledgePack(
            pack_id=str(uuid.uuid4()),
            hostname=hostname,
            archetype=best_archetype,
            patterns=final_patterns,
            visual_signature=visual_signature,
            region_knowledge=region_knowledge,
            concept_knowledge=concept_knowledge,
            page_variants=page_variants,
            snapshots_used=snapshot_ids,
            graph=graph.model_dump() if graph else None,
            knowledge_confidence=knowledge_confidence,
            generated_at=datetime.now(timezone.utc).isoformat()
        )
        return pack
