import os

from pydantic import BaseModel

from .models import SiteSnapshot
from .storage import CaptureStorage


class CaptureSummary(BaseModel):
    snapshot_id: str
    url: str
    hostname: str
    title: str
    captured_at: str
    semantic_count: int
    layout_count: int
    dom_size_bytes: int
    screenshot_size_bytes: int


class CaptureHealth(BaseModel):
    score: float

    semantic_score: float
    layout_score: float

    warnings: list[str]


def get_capture_summary(storage: CaptureStorage, snapshot_id: str) -> CaptureSummary | None:
    """Load a snapshot and compute file-size metrics."""
    snapshot = storage.load_snapshot(snapshot_id)
    if snapshot is None:
        return None

    # Read file sizes from disk
    screenshot_size = 0
    dom_size = 0

    screenshot_file = os.path.join(storage.base_dir, snapshot_id, "screenshot.png")
    if os.path.isfile(screenshot_file):
        screenshot_size = os.path.getsize(screenshot_file)

    dom_file = os.path.join(storage.base_dir, snapshot_id, "dom.html")
    if os.path.isfile(dom_file):
        dom_size = os.path.getsize(dom_file)

    return CaptureSummary(
        snapshot_id=snapshot.snapshot_id,
        url=snapshot.url,
        hostname=snapshot.hostname,
        title=snapshot.title,
        captured_at=snapshot.captured_at,
        semantic_count=len(snapshot.semantic_elements),
        layout_count=len(snapshot.layout_elements),
        dom_size_bytes=dom_size,
        screenshot_size_bytes=screenshot_size,
    )


def get_capture_health(storage: CaptureStorage, snapshot_id: str) -> CaptureHealth | None:
    """Score the quality of a capture and flag potential issues."""
    snapshot = storage.load_snapshot(snapshot_id)
    if snapshot is None:
        return None

    warnings: list[str] = []
    semantic_count = len(snapshot.semantic_elements)
    layout_count = len(snapshot.layout_elements)

    # --- Semantic score ---
    # Expect at least 10 semantic elements for a typical page
    if semantic_count == 0:
        semantic_score = 0.0
        warnings.append("No semantic elements captured")
    elif semantic_count < 5:
        semantic_score = 0.3
        warnings.append(f"Very few semantic elements ({semantic_count})")
    elif semantic_count < 10:
        semantic_score = 0.6
    else:
        semantic_score = 1.0

    # --- Layout score ---
    if layout_count == 0:
        layout_score = 0.0
        warnings.append("No layout elements captured")
    elif layout_count >= 500:
        layout_score = 0.7
        warnings.append("Layout capture truncated at 500 elements")
    elif layout_count < 5:
        layout_score = 0.3
        warnings.append(f"Very few layout elements ({layout_count})")
    else:
        layout_score = 1.0

    # Suspicious ratio: layout >> semantic
    if semantic_count > 0 and layout_count / max(semantic_count, 1) > 50:
        warnings.append(
            f"Suspicious ratio: {layout_count} layout vs {semantic_count} semantic elements"
        )

    # DOM size check
    dom_file = os.path.join(storage.base_dir, snapshot_id, "dom.html")
    if os.path.isfile(dom_file):
        dom_size = os.path.getsize(dom_file)
        if dom_size > 10 * 1024 * 1024:  # 10 MB
            warnings.append(f"DOM size exceeds 10MB ({dom_size / 1024 / 1024:.1f}MB)")
        elif dom_size > 5 * 1024 * 1024:  # 5 MB
            warnings.append(f"DOM size is large ({dom_size / 1024 / 1024:.1f}MB)")

    # Overall score (weighted average)
    score = round(semantic_score * 0.5 + layout_score * 0.5, 2)

    return CaptureHealth(
        score=score,
        semantic_score=semantic_score,
        layout_score=layout_score,
        warnings=warnings,
    )
