import os
import json
import shutil
from typing import List, Optional
from datetime import datetime

from .models import TransformationHistoryRecord

class HistoryService:
    def __init__(self, base_dir: str = "data/history"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save_record(self, record: TransformationHistoryRecord) -> TransformationHistoryRecord:
        """
        Saves the history record immutably.
        Copies the screenshot files into the run directory.
        """
        run_dir = os.path.join(self.base_dir, record.run_id)
        os.makedirs(run_dir, exist_ok=True)
        
        # Copy screenshots
        if record.before_screenshot_path and os.path.exists(record.before_screenshot_path):
            new_before = os.path.join(run_dir, "before.png")
            shutil.copy2(record.before_screenshot_path, new_before)
            record.before_screenshot_path = new_before.replace("\\", "/")
            
        if record.after_screenshot_path and os.path.exists(record.after_screenshot_path):
            new_after = os.path.join(run_dir, "after.png")
            shutil.copy2(record.after_screenshot_path, new_after)
            record.after_screenshot_path = new_after.replace("\\", "/")
            
        if record.reference_screenshot_path and os.path.exists(record.reference_screenshot_path):
            new_ref = os.path.join(run_dir, "reference.png")
            shutil.copy2(record.reference_screenshot_path, new_ref)
            record.reference_screenshot_path = new_ref.replace("\\", "/")
            
        # Save JSON
        record_path = os.path.join(run_dir, "record.json")
        with open(record_path, "w", encoding="utf-8") as f:
            f.write(record.model_dump_json(indent=2))
            
        return record

    def list_records(self) -> List[TransformationHistoryRecord]:
        records = []
        for run_id in os.listdir(self.base_dir):
            run_dir = os.path.join(self.base_dir, run_id)
            record_path = os.path.join(run_dir, "record.json")
            if os.path.isfile(record_path):
                try:
                    with open(record_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        records.append(TransformationHistoryRecord(**data))
                except Exception as e:
                    print(f"Failed to load record {run_id}: {e}")
        
        # Sort by timestamp descending
        records.sort(key=lambda x: x.timestamp, reverse=True)
        return records

    def get_record(self, run_id: str) -> Optional[TransformationHistoryRecord]:
        record_path = os.path.join(self.base_dir, run_id, "record.json")
        if not os.path.exists(record_path):
            return None
        with open(record_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return TransformationHistoryRecord(**data)
