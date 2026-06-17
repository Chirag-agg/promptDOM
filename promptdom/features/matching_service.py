from datetime import datetime, timezone
from typing import List, Dict, Any
from .store import FeatureStore
from .matcher import FeatureMatcher
from .matching_models import MatchResult, FeatureMatch, DiagnosticsResult
from ..inspection.service import InspectionService

def get_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"

class FeatureMatchingService:
    def __init__(self, store: FeatureStore, inspection_service: InspectionService, matcher: FeatureMatcher):
        self.store = store
        self.inspection_service = inspection_service
        self.matcher = matcher

    async def get_matches(self) -> MatchResult:
        features = self.store.list_features()
        if not features:
            return MatchResult(page_hostname="unknown", page_type="unknown", matches=[])

        try:
            page_context = await self.inspection_service.inspect()
            hostname = page_context.hostname
            page_type = page_context.page_type
        except Exception:
            hostname = "unknown"
            page_type = "unknown"

        result = await self.matcher.match(hostname, page_type, features)
        
        for match in result.matches:
            if match.feature_health < 1.0 and match.status != "disabled" and match.status != "stale":
                # Ensure diagnostic precision: if target is completely missing on a matched page, it's stale.
                match.status = "stale"
                match.reason = "Target could not be found on the matched page"

            # Cache the status and last seen timestamp
            self.store.update_feature(match.feature_id, {
                "last_status": match.status,
                "last_seen_at": get_utc_now()
            })

        return result

    async def get_diagnostics(self) -> DiagnosticsResult:
        result = await self.get_matches()
        
        total = len(result.matches)
        ready = sum(1 for m in result.matches if m.status == "ready")
        partial = sum(1 for m in result.matches if m.status == "partial")
        stale = sum(1 for m in result.matches if m.status == "stale")
        disabled = sum(1 for m in result.matches if m.status == "disabled")

        return DiagnosticsResult(
            total_features=total,
            ready=ready,
            partial=partial,
            stale=stale,
            disabled=disabled
        )
