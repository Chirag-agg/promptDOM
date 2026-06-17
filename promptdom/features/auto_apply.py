import time
from typing import Set, Tuple
from .matching_service import FeatureMatchingService
from .store import FeatureStore
from .auto_apply_models import AutoApplyResult, AppliedFeature
from typing import List, Optional
from ..runtime.engine import RuntimeEngine
from ..inspection.service import InspectionService
from ..browser import BrowserManager
from ..analytics.collector import AnalyticsCollector
from ..analytics.models import ApplicationLog

class AppliedFeatureCache:
    def __init__(self):
        # Stores tuples of (feature_id, page_url, dom_fingerprint)
        self.cache: Set[Tuple[str, str, str]] = set()

    def has_applied(self, feature_id: str, page_url: str, dom_fingerprint: str) -> bool:
        return (feature_id, page_url, dom_fingerprint) in self.cache

    def mark_applied(self, feature_id: str, page_url: str, dom_fingerprint: str):
        self.cache.add((feature_id, page_url, dom_fingerprint))

class AutoApplyService:
    def __init__(
        self, 
        matching_service: FeatureMatchingService,
        store: FeatureStore,
        runtime: RuntimeEngine,
        inspection_service: InspectionService,
        browser_manager: BrowserManager,
        analytics_collector: AnalyticsCollector
    ):
        self.matching_service = matching_service
        self.store = store
        self.runtime = runtime
        self.inspection_service = inspection_service
        self.browser_manager = browser_manager
        self.analytics_collector = analytics_collector
        self.cache = AppliedFeatureCache()

    async def apply_features(self, dry_run: bool = False) -> AutoApplyResult:
        try:
            page_info = await self.browser_manager.get_active_tab_info()
            page_url = page_info.get("url", "unknown")
            page_context = await self.inspection_service.inspect()
            dom_fingerprint = page_context.dom_fingerprint
        except Exception:
            page_url = "unknown"
            dom_fingerprint = "unknown"

        match_result = await self.matching_service.get_matches()
        
        results = []
        applied_count = 0
        skipped_count = 0
        failed_count = 0
        
        for match in match_result.matches:
            if match.status != "ready":
                skipped_count += 1
                continue
                
            if not dry_run and self.cache.has_applied(match.feature_id, page_url, dom_fingerprint):
                skipped_count += 1
                continue
                
            feature = self.store.get_feature(match.feature_id)
            if not feature:
                skipped_count += 1
                continue

            start_time = time.perf_counter()
            success = False
            msg = ""

            if dry_run:
                success = True
                msg = "Dry run: would execute"
            else:
                try:
                    success = await self.runtime.execute(feature.action, feature.selector, self.browser_manager)
                    if success:
                        msg = "Successfully executed"
                        self.cache.mark_applied(match.feature_id, page_url, dom_fingerprint)
                    else:
                        msg = "Execution failed"
                        failed_count += 1
                except Exception as e:
                    success = False
                    msg = str(e)
                    failed_count += 1

            execution_time_ms = (time.perf_counter() - start_time) * 1000.0

            if success:
                applied_count += 1

            if not dry_run:
                self.analytics_collector.log_application(ApplicationLog(
                    feature_id=match.feature_id,
                    success=success,
                    execution_time_ms=round(execution_time_ms, 2),
                    page_url=page_url
                ))

            results.append(AppliedFeature(
                feature_id=match.feature_id,
                feature_name=match.feature_name,
                success=success,
                execution_time_ms=round(execution_time_ms, 2),
                message=msg,
                page_url=page_url
            ))

        return AutoApplyResult(
            total_matches=len(match_result.matches),
            applied_count=applied_count,
            skipped_count=skipped_count,
            failed_count=failed_count,
            results=results
        )
