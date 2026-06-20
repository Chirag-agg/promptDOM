from promptdom.capture.models import SiteSnapshot
from promptdom.intelligence.models import WebsiteModel, RegionType
from .models import WebsiteArchetype, WebsitePattern, ArchetypeResult


class ArchetypeDetector:
    """Heuristically detects the underlying archetype of a website."""

    def detect(self, snapshot: SiteSnapshot, website_model: WebsiteModel) -> ArchetypeResult:
        scores = {arc: 0 for arc in WebsiteArchetype if arc != WebsiteArchetype.UNKNOWN}
        evidence = []
        patterns = set()

        # Lookups
        semantic_tags = {el.tag for el in snapshot.semantic_elements}
        region_types = {r.region_type for r in website_model.regions}
        region_by_type = {r.region_type: r for r in website_model.regions}
        
        has_videos = "video" in semantic_tags or "iframe" in semantic_tags

        # MEDIA_PLATFORM rules
        if has_videos:
            scores[WebsiteArchetype.MEDIA_PLATFORM] += 10
            evidence.append("Video/iframe elements detected (+10 MEDIA)")
            patterns.add(WebsitePattern.VIDEO_GRID)

        # FORUM / FEED / SOCIAL rules
        if RegionType.FEED in region_types or "article" in semantic_tags:
            scores[WebsiteArchetype.FORUM] += 5
            scores[WebsiteArchetype.CONTENT_FEED_PLATFORM] += 8
            scores[WebsiteArchetype.SOCIAL_NETWORK] += 6
            evidence.append("Feed region/article tags detected (+8 FEED, +6 SOCIAL, +5 FORUM)")
            patterns.add(WebsitePattern.CARD_FEED)

        # PRODUCTIVITY / DASHBOARD rules
        if RegionType.SIDEBAR in region_types:
            scores[WebsiteArchetype.PRODUCTIVITY_APP] += 5
            scores[WebsiteArchetype.DASHBOARD] += 4
            evidence.append("Sidebar detected (+5 PROD, +4 DASHBOARD)")
            patterns.add(WebsitePattern.LEFT_SIDEBAR_LAYOUT)

        if "table" in semantic_tags or "canvas" in semantic_tags:
            scores[WebsiteArchetype.DASHBOARD] += 6
            scores[WebsiteArchetype.PRODUCTIVITY_APP] += 3
            evidence.append("Table/Canvas elements detected (+6 DASHBOARD, +3 PROD)")
            patterns.add(WebsitePattern.DASHBOARD_WIDGETS)

        # ECOMMERCE rules
        price_indicators = sum(1 for el in snapshot.semantic_elements if el.text and ("$" in el.text or "€" in el.text or "£" in el.text))
        if price_indicators >= 3:
            scores[WebsiteArchetype.ECOMMERCE] += 12
            evidence.append(f"Price indicators detected ({price_indicators}) (+12 ECOMMERCE)")
            patterns.add(WebsitePattern.PRODUCT_GRID)

        # SEARCH_ENGINE rules
        if RegionType.FORM in region_types and RegionType.FEED not in region_types and RegionType.SIDEBAR not in region_types:
            form = region_by_type[RegionType.FORM]
            if form.width > 250:
                scores[WebsiteArchetype.SEARCH_ENGINE] += 10
                evidence.append("Large form without sidebars/feeds detected (+10 SEARCH)")
                patterns.add(WebsitePattern.SEARCH_CENTRIC)
                
        # Additional Header/Nav
        if RegionType.HEADER in region_types or RegionType.NAVIGATION in region_types:
            patterns.add(WebsitePattern.TOP_NAV_LAYOUT)

        # Evaluate winner
        total_score = sum(scores.values())
        if total_score == 0:
            return ArchetypeResult(
                snapshot_id=snapshot.snapshot_id,
                archetype=WebsiteArchetype.UNKNOWN,
                confidence=0.0,
                evidence=["No distinct archetype signals detected."],
                competing_archetypes=[],
                archetype_scores={},
                patterns=[]
            )

        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        winner, winner_score = sorted_scores[0]
        confidence = winner_score / total_score

        competing = [arc.value for arc, score in sorted_scores[1:] if score > 0]

        return ArchetypeResult(
            snapshot_id=snapshot.snapshot_id,
            archetype=winner,
            confidence=round(confidence, 2),
            evidence=evidence,
            competing_archetypes=competing,
            archetype_scores={arc.value: score for arc, score in sorted_scores if score > 0},
            patterns=list(patterns)
        )
