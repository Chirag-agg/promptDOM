import os
from typing import List, Union
from .models import ApplicationLog, RepairLog, LLMRequestLog, PlanningLog

class AnalyticsCollector:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.applications_file = os.path.join(self.data_dir, "applications.jsonl")
        self.repairs_file = os.path.join(self.data_dir, "repairs.jsonl")
        self.llm_requests_file = os.path.join(self.data_dir, "llm_requests.jsonl")
        self.planning_requests_file = os.path.join(self.data_dir, "planning_requests.jsonl")

    def _append_log(self, filepath: str, log: Union[ApplicationLog, RepairLog, LLMRequestLog, PlanningLog]):
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(log.model_dump_json() + "\n")

    def log_application(self, log: ApplicationLog):
        self._append_log(self.applications_file, log)

    def log_repair(self, log: RepairLog):
        self._append_log(self.repairs_file, log)

    def log_llm_request(self, log: LLMRequestLog):
        self._append_log(self.llm_requests_file, log)

    def log_planning_request(self, log: PlanningLog):
        self._append_log(self.planning_requests_file, log)

    def get_application_logs(self) -> List[ApplicationLog]:
        if not os.path.exists(self.applications_file):
            return []
        logs = []
        with open(self.applications_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(ApplicationLog.model_validate_json(line))
        return logs

    def get_repair_logs(self) -> List[RepairLog]:
        if not os.path.exists(self.repairs_file):
            return []
        logs = []
        with open(self.repairs_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(RepairLog.model_validate_json(line))
        return logs

    def get_llm_request_logs(self) -> List[LLMRequestLog]:
        if not os.path.exists(self.llm_requests_file):
            return []
        logs = []
        with open(self.llm_requests_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(LLMRequestLog.model_validate_json(line))
        return logs

    def get_planning_logs(self) -> List[PlanningLog]:
        if not os.path.exists(self.planning_requests_file):
            return []
        logs = []
        with open(self.planning_requests_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(PlanningLog.model_validate_json(line))
        return logs
