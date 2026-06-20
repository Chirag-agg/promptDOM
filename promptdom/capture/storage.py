import os
import json
from typing import Optional

from .models import SiteSnapshot


class CaptureStorage:
    """File-system storage for site capture snapshots.

    Layout:
        data/captures/<snapshot_id>/
            record.json      — SiteSnapshot metadata
            screenshot.png    — page screenshot
            dom.html          — cleaned DOM
    """

    def __init__(self, base_dir: str = "data/captures"):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def save_snapshot(
        self,
        snapshot: SiteSnapshot,
        screenshot_bytes: bytes,
        dom_html: str,
    ) -> SiteSnapshot:
        """Persist a snapshot: write record.json, screenshot.png, and dom.html."""
        snap_dir = os.path.join(self.base_dir, snapshot.snapshot_id)
        os.makedirs(snap_dir, exist_ok=True)

        # Write screenshot
        screenshot_path = os.path.join(snap_dir, "screenshot.png")
        with open(screenshot_path, "wb") as f:
            f.write(screenshot_bytes)

        # Write cleaned DOM
        dom_path = os.path.join(snap_dir, "dom.html")
        with open(dom_path, "w", encoding="utf-8") as f:
            f.write(dom_html)

        # Normalize paths in model to use forward slashes
        snapshot.screenshot_path = screenshot_path.replace("\\", "/")
        snapshot.dom_path = dom_path.replace("\\", "/")

        # Write metadata
        record_path = os.path.join(snap_dir, "record.json")
        with open(record_path, "w", encoding="utf-8") as f:
            f.write(snapshot.model_dump_json(indent=2))

        return snapshot

    def load_snapshot(self, snapshot_id: str) -> Optional[SiteSnapshot]:
        """Load a snapshot by ID. Returns None if not found."""
        record_path = os.path.join(self.base_dir, snapshot_id, "record.json")
        if not os.path.exists(record_path):
            return None

        with open(record_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return SiteSnapshot(**data)

    def list_snapshots(self) -> list[SiteSnapshot]:
        """List all stored snapshots, sorted by captured_at descending."""
        snapshots: list[SiteSnapshot] = []

        if not os.path.exists(self.base_dir):
            return snapshots

        for entry in os.listdir(self.base_dir):
            record_path = os.path.join(self.base_dir, entry, "record.json")
            if os.path.isfile(record_path):
                try:
                    with open(record_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        snapshots.append(SiteSnapshot(**data))
                except Exception as e:
                    print(f"Failed to load snapshot {entry}: {e}")

        snapshots.sort(key=lambda s: s.captured_at, reverse=True)
        return snapshots
