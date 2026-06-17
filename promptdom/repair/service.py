from typing import List
from datetime import datetime, timezone
from ..features.store import FeatureStore
from ..features.models import Feature
from ..inspection.service import InspectionService
from ..resolution.resolver import SemanticResolver
from ..analytics.collector import AnalyticsCollector
from ..analytics.models import RepairLog
from .updater import SelectorVerifier
from .models import RepairAttempt, RepairResult

def get_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat() + "Z"

class FeatureRepairService:
    def __init__(
        self,
        store: FeatureStore,
        inspection_service: InspectionService,
        resolver: SemanticResolver,
        verifier: SelectorVerifier,
        analytics_collector: AnalyticsCollector
    ):
        self.store = store
        self.inspection_service = inspection_service
        self.resolver = resolver
        self.verifier = verifier
        self.analytics_collector = analytics_collector

    async def get_stale_features(self) -> List[Feature]:
        try:
            inspection_context = await self.inspection_service.inspect()
            hostname = inspection_context.hostname
            resolution_inspection = await self.inspection_service.inspect_resolution()
        except Exception:
            return []

        alive_selectors = self.verifier.get_alive_selectors(resolution_inspection)
        
        all_features = self.store.list_features()
        stale_features = []
        for feature in all_features:
            if feature.hostname == hostname and feature.selector not in alive_selectors:
                stale_features.append(feature)
                
        return stale_features

    async def repair_features(self, dry_run: bool = False) -> RepairResult:
        stale_features = await self.get_stale_features()
        
        if not stale_features:
            return RepairResult(repaired_count=0, failed_count=0, attempts=[])
            
        resolution_inspection = await self.inspection_service.inspect_resolution()
        alive_selectors = self.verifier.get_alive_selectors(resolution_inspection)

        attempts = []
        repaired_count = 0
        failed_count = 0

        for feature in stale_features:
            resolution = await self.resolver.resolve(feature.target, feature.target_type)
            
            success = False
            reason = ""
            new_selector = resolution.selector

            if not resolution.matched:
                success = False
                reason = "Resolver could not find semantic target"
            elif resolution.confidence < 0.85:
                success = False
                reason = f"Confidence {resolution.confidence} too low (requires >= 0.85)"
            elif new_selector not in alive_selectors:
                success = False
                reason = "Proposed selector does not exist in active DOM"
            elif new_selector == feature.selector:
                success = False
                reason = "Proposed selector is identical to the broken selector"
            else:
                success = True
                reason = "High confidence repair verified successfully"

            attempts.append(RepairAttempt(
                feature_id=feature.id,
                old_selector=feature.selector,
                new_selector=new_selector if resolution.matched else "",
                success=success,
                confidence=resolution.confidence,
                reason=reason,
                repair_method="semantic_resolver"
            ))

            if success:
                repaired_count += 1
                if not dry_run:
                    self.analytics_collector.log_repair(RepairLog(
                        feature_id=feature.id,
                        old_selector=feature.selector,
                        new_selector=new_selector,
                        confidence=resolution.confidence,
                        repair_method="semantic_resolver"
                    ))
                        
                    updates = {
                        "selector": new_selector,
                        "repair_count": feature.repair_count + 1,
                        "last_repaired_at": get_utc_now()
                    }
                    self.store.update_feature(feature.id, updates)
            else:
                failed_count += 1

        return RepairResult(
            repaired_count=repaired_count,
            failed_count=failed_count,
            attempts=attempts
        )
