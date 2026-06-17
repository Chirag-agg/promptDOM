from typing import List
from .models import Feature
from .matching_models import FeatureMatch, MatchResult
from ..resolution.resolver import SemanticResolver

class FeatureMatcher:
    def __init__(self, resolver: SemanticResolver):
        self.resolver = resolver

    async def match(self, page_hostname: str, page_type: str, features: List[Feature]) -> MatchResult:
        matches = []
        for feature in features:
            if not feature.enabled:
                matches.append(FeatureMatch(
                    feature_id=feature.id,
                    feature_name=feature.name,
                    confidence=0.0,
                    feature_health=1.0,
                    status="disabled",
                    reason="Feature is disabled."
                ))
                continue

            score = 0.0
            reasons = []
            
            # Stage 1: Cheap Checks
            hostname_match = (feature.hostname == page_hostname)
            type_match = (feature.page_type == page_type)

            if hostname_match:
                score += 0.5
                reasons.append("Hostname matched")
            else:
                reasons.append("Hostname mismatch")
                
            if type_match:
                score += 0.3
                reasons.append("Page type matched")
            else:
                reasons.append("Page type mismatch")

            if not hostname_match and not type_match:
                # Early exit - doesn't apply to this page at all
                matches.append(FeatureMatch(
                    feature_id=feature.id,
                    feature_name=feature.name,
                    confidence=score,
                    feature_health=1.0, # Health only drops if the target breaks on the CORRECT page
                    status="partial",
                    reason=", ".join(reasons) + "."
                ))
                continue

            # Stage 2: Expensive Semantic Check
            resolution = await self.resolver.resolve(feature.target, feature.target_type)
            target_exists = resolution.matched
            
            feature_health = 1.0 if target_exists else 0.0

            if target_exists:
                score += 0.2
                reasons.append("Target matched")
                status = "ready"
            else:
                reasons.append("Target missing")
                status = "stale"
                
            if score < 1.0 and status == "ready":
                status = "partial"

            matches.append(FeatureMatch(
                feature_id=feature.id,
                feature_name=feature.name,
                confidence=score,
                feature_health=feature_health,
                status=status,
                reason=", ".join(reasons) + "."
            ))

        return MatchResult(
            page_hostname=page_hostname,
            page_type=page_type,
            matches=matches
        )
