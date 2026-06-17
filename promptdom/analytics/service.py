from datetime import datetime, timezone
from typing import List, Dict, Any
from .models import FeatureAnalytics, SiteAnalytics, SystemHealth, FeatureTimeline, RecentAnalytics, PlannerAnalytics, PlannerDisagreementMetrics
from .collector import AnalyticsCollector
from ..features.store import FeatureStore

def calculate_days_since(iso_time: str) -> float:
    try:
        t = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - t
        return max(1.0, delta.total_seconds() / 86400.0)
    except Exception:
        return 1.0

class AnalyticsService:
    def __init__(self, store: FeatureStore, collector: AnalyticsCollector):
        self.store = store
        self.collector = collector

    def get_feature_analytics(self) -> List[FeatureAnalytics]:
        features = self.store.list_features()
        applications = self.collector.get_application_logs()
        
        analytics = []
        for feature in features:
            apps = [a for a in applications if a.feature_id == feature.id]
            apply_count = len(apps)
            success_count = sum(1 for a in apps if a.success)
            success_rate = success_count / apply_count if apply_count > 0 else 0.0
            
            total_time = sum(a.execution_time_ms for a in apps if a.success)
            avg_time = total_time / success_count if success_count > 0 else 0.0
            
            age_days = calculate_days_since(feature.created_at)
            decay_score = feature.repair_count / age_days
            
            analytics.append(FeatureAnalytics(
                name=feature.name,
                apply_count=apply_count,
                success_rate=round(success_rate, 2),
                repair_count=feature.repair_count,
                average_execution_ms=round(avg_time, 2),
                feature_decay_score=round(decay_score, 4),
                last_seen_at=feature.last_seen_at
            ))
            
        return analytics

    def get_site_analytics(self) -> List[SiteAnalytics]:
        features = self.store.list_features()
        
        sites: Dict[str, SiteAnalytics] = {}
        for feature in features:
            if feature.hostname not in sites:
                sites[feature.hostname] = SiteAnalytics(
                    hostname=feature.hostname,
                    feature_count=0,
                    stale_features=0,
                    repair_count=0
                )
            
            site = sites[feature.hostname]
            site.feature_count += 1
            if feature.last_status == "stale":
                site.stale_features += 1
            site.repair_count += feature.repair_count
            
        return list(sites.values())

    def get_planner_analytics(self) -> PlannerAnalytics:
        logs = self.collector.get_planning_logs()
        
        rule_usage = 0
        llm_usage = 0
        hybrid_rule_usage = 0
        hybrid_llm_usage = 0
        total_time = 0.0
        
        for log in logs:
            if log.planner_source == "RULE":
                rule_usage += 1
            elif log.planner_source == "LLM":
                llm_usage += 1
            elif log.planner_source == "HYBRID_RULE":
                hybrid_rule_usage += 1
            elif log.planner_source == "HYBRID_LLM":
                hybrid_llm_usage += 1
            total_time += log.execution_time_ms
            
        count = len(logs)
        return PlannerAnalytics(
            rule_usage=rule_usage,
            llm_usage=llm_usage,
            hybrid_rule_usage=hybrid_rule_usage,
            hybrid_llm_usage=hybrid_llm_usage,
            average_latency_ms=total_time / count if count > 0 else 0.0
        )

    def get_planner_disagreement(self) -> PlannerDisagreementMetrics:
        logs = self.collector.get_planner_comparisons()
        if not logs:
            return PlannerDisagreementMetrics(disagreement_rate=0.0, sample_count=0)
        
        disagreements = sum(1 for log in logs if not log.agreed)
        return PlannerDisagreementMetrics(
            disagreement_rate=disagreements / len(logs),
            sample_count=len(logs)
        )

    def get_system_health(self) -> SystemHealth:
        features = self.store.list_features()
        
        total = len(features)
        ready = sum(1 for f in features if f.last_status == "ready")
        stale = sum(1 for f in features if f.last_status == "stale")
        disabled = sum(1 for f in features if not f.enabled)
        
        # Currently we only log successful repairs to repairs.jsonl,
        # so repair_success_rate is essentially 1.0 from the log's perspective.
        repair_success_rate = 1.0
        
        return SystemHealth(
            total_features=total,
            ready_features=ready,
            stale_features=stale,
            disabled_features=disabled,
            repair_success_rate=repair_success_rate
        )

    def get_feature_timeline(self, feature_id: str) -> FeatureTimeline:
        feature = self.store.get_feature(feature_id)
        if not feature:
            raise ValueError("Feature not found")
            
        apps = [a for a in self.collector.get_application_logs() if a.feature_id == feature_id]
        reps = [r for r in self.collector.get_repair_logs() if r.feature_id == feature_id]
        
        return FeatureTimeline(
            created_at=feature.created_at,
            applications=sorted(apps, key=lambda x: x.timestamp, reverse=True),
            repairs=sorted(reps, key=lambda x: x.timestamp, reverse=True)
        )

    def get_recent_events(self) -> RecentAnalytics:
        apps = sorted(self.collector.get_application_logs(), key=lambda x: x.timestamp, reverse=True)[:50]
        reps = sorted(self.collector.get_repair_logs(), key=lambda x: x.timestamp, reverse=True)[:50]
        
        return RecentAnalytics(
            applications=apps,
            repairs=reps
        )
