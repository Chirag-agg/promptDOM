import uuid
from typing import Dict, List, Tuple

from promptdom.capture.models import SiteSnapshot, LayoutElement, SemanticElement
from .models import RegionType, PageRegion, WebsiteModel


class WebsiteAnalyzer:
    """Analyzes a SiteSnapshot to extract structured website regions using deterministic heuristics."""

    def analyze(self, snapshot: SiteSnapshot) -> WebsiteModel:
        regions: list[PageRegion] = []

        # 1. Estimate Viewport/Page bounds
        max_x = max([el.x + el.width for el in snapshot.layout_elements if el.visible], default=1920.0)
        max_y = max([el.y + el.height for el in snapshot.layout_elements if el.visible], default=1080.0)
        viewport_width = min(max_x, 1920.0) if max_x > 0 else 1920.0
        viewport_height = min(max_y, 1080.0) if max_y > 0 else 1080.0

        # Maps for quick lookup
        semantic_by_selector = {el.selector: el for el in snapshot.semantic_elements}
        layout_by_selector = {el.selector: el for el in snapshot.layout_elements}

        # Dictionary to accumulate candidates for each region type
        candidates: Dict[RegionType, List[Tuple[LayoutElement, SemanticElement | None, List[str]]]] = {
            RegionType.HEADER: [],
            RegionType.NAVIGATION: [],
            RegionType.SIDEBAR: [],
            RegionType.MAIN_CONTENT: [],
            RegionType.FEED: [],
            RegionType.FOOTER: [],
            RegionType.FORM: [],
        }

        # Pass 1: Semantic Anchors (highest confidence)
        for sem in snapshot.semantic_elements:
            layout = layout_by_selector.get(sem.selector)
            if not layout or not layout.visible or layout.width < 10 or layout.height < 10:
                continue

            if sem.tag == "header" or sem.role == "banner":
                candidates[RegionType.HEADER].append((layout, sem, ["Matched <header> tag or banner role"]))
            elif sem.tag == "nav" or sem.role == "navigation":
                candidates[RegionType.NAVIGATION].append((layout, sem, ["Matched <nav> tag or navigation role"]))
            elif sem.tag == "footer" or sem.role == "contentinfo":
                candidates[RegionType.FOOTER].append((layout, sem, ["Matched <footer> tag or contentinfo role"]))
            elif sem.tag == "main" or sem.role == "main":
                candidates[RegionType.MAIN_CONTENT].append((layout, sem, ["Matched <main> tag or main role"]))
            elif sem.tag == "aside" or sem.role == "complementary":
                candidates[RegionType.SIDEBAR].append((layout, sem, ["Matched <aside> tag or complementary role"]))
            elif sem.tag == "form":
                candidates[RegionType.FORM].append((layout, sem, ["Matched <form> tag"]))

        # Pass 2: Positional/Size Heuristics
        for layout in snapshot.layout_elements:
            if not layout.visible or layout.width < 50 or layout.height < 20:
                continue

            area = layout.width * layout.height
            sem = semantic_by_selector.get(layout.selector)

            # Positional Header: top 15%, wide
            if layout.y < viewport_height * 0.15 and layout.width > viewport_width * 0.8:
                candidates[RegionType.HEADER].append((layout, sem, ["Top 15% of viewport", "Wide (>80% viewport)"]))

            # Positional Footer: bottom area, wide
            if max_y > 0 and layout.y > max_y - viewport_height * 0.2 and layout.width > viewport_width * 0.8:
                candidates[RegionType.FOOTER].append((layout, sem, ["Bottom 20% of page", "Wide (>80% viewport)"]))

            # Positional Sidebar: tall, narrow, left or right
            if layout.height > viewport_height * 0.5 and 40 < layout.width < viewport_width * 0.35:
                if layout.x < viewport_width * 0.3 or layout.x > viewport_width * 0.7:
                    candidates[RegionType.SIDEBAR].append((layout, sem, ["Tall (>50% viewport)", "Narrow", "Left/Right aligned"]))

            # Main Content fallback: large central area
            if area > viewport_width * viewport_height * 0.2 and layout.width > viewport_width * 0.4:
                if layout.y >= 0:  # Allow x=0 since structural wrappers often touch the left edge
                    candidates[RegionType.MAIN_CONTENT].append((layout, sem, ["Large area (>20% viewport)", "Central positioning"]))

        # Resolve best candidates and deduplicate
        used_selectors = set(["body", "html", "#root", "#app", "div#root", "div#__next", "main", "div.app-container"])

        for region_type, item_candidates in candidates.items():
            if not item_candidates:
                continue

            # Scoring function to pick the best candidate
            def score_candidate(c: Tuple[LayoutElement, SemanticElement | None, List[str]]) -> float:
                layout, sem, evidence = c
                score = 0.0
                if any("Matched <" in e for e in evidence):
                    score += 0.8

                area_ratio = (layout.width * layout.height) / (viewport_width * viewport_height) if viewport_width and viewport_height else 0

                if region_type == RegionType.MAIN_CONTENT:
                    score += min(area_ratio, 1.0) * 0.4
                elif region_type == RegionType.SIDEBAR:
                    score += min(layout.height / viewport_height, 1.0) * 0.2
                else:
                    score += min(area_ratio, 1.0) * 0.1

                return score

            # Sort descending
            item_candidates.sort(key=score_candidate, reverse=True)

            best_layout, best_sem, best_evidence = None, None, None
            for layout, sem, evidence in item_candidates:
                if layout.selector not in used_selectors:
                    best_layout, best_sem, best_evidence = layout, sem, evidence
                    break

            if not best_layout:
                # If all were skipped because they are used or roots, take the highest scoring one anyway if it's semantic
                fallback = item_candidates[0]
                if any("Matched <" in e for e in fallback[2]):
                    best_layout, best_sem, best_evidence = fallback
                else:
                    continue

            used_selectors.add(best_layout.selector)

            confidence = min(score_candidate((best_layout, best_sem, best_evidence)) + 0.2, 1.0)
            if any("Matched <" in e for e in best_evidence):
                confidence = max(confidence, 0.9)

            regions.append(PageRegion(
                region_id=str(uuid.uuid4()),
                region_type=region_type,
                selector=best_layout.selector,
                x=best_layout.x,
                y=best_layout.y,
                width=best_layout.width,
                height=best_layout.height,
                confidence=round(confidence, 2),
                evidence=best_evidence
            ))

        return WebsiteModel(
            snapshot_id=snapshot.snapshot_id,
            regions=regions,
            detected_patterns=[]
        )
