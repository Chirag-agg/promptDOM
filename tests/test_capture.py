"""Tests for the Universal Site Capture Engine (Phase 9.0 + 9.1)."""

import json
import os
import shutil
import tempfile

import pytest

from promptdom.capture.models import SemanticElement, LayoutElement, SiteSnapshot
from promptdom.capture.extractor import clean_dom
from promptdom.capture.storage import CaptureStorage
from promptdom.capture.analytics import (
    CaptureSummary, CaptureHealth,
    get_capture_summary, get_capture_health,
)


# ---------------------------------------------------------------------------
# Model tests
# ---------------------------------------------------------------------------

class TestSemanticElement:
    def test_minimal(self):
        el = SemanticElement(tag="button", selector="button#submit")
        assert el.tag == "button"
        assert el.selector == "button#submit"
        assert el.text is None
        assert el.aria_label is None
        assert el.role is None

    def test_full(self):
        el = SemanticElement(
            tag="a",
            text="Home",
            aria_label="Go to home page",
            role="link",
            selector="a#home",
        )
        assert el.text == "Home"
        assert el.aria_label == "Go to home page"
        assert el.role == "link"

    def test_roundtrip_json(self):
        el = SemanticElement(tag="input", text="Search", selector="input#q")
        data = json.loads(el.model_dump_json())
        restored = SemanticElement(**data)
        assert restored == el


class TestLayoutElement:
    def test_create(self):
        el = LayoutElement(
            selector="button#save", x=10.0, y=20.0, width=100.0, height=40.0, visible=True
        )
        assert el.x == 10.0
        assert el.visible is True

    def test_roundtrip_json(self):
        el = LayoutElement(
            selector="div#main", x=0, y=0, width=1920, height=1080, visible=True
        )
        data = json.loads(el.model_dump_json())
        restored = LayoutElement(**data)
        assert restored == el


class TestSiteSnapshot:
    def test_create(self):
        snap = SiteSnapshot(
            snapshot_id="abc-123",
            url="https://example.com",
            hostname="example.com",
            title="Example",
            captured_at="2026-01-01T00:00:00",
            semantic_elements=[],
            layout_elements=[],
            screenshot_path="data/captures/abc-123/screenshot.png",
            dom_path="data/captures/abc-123/dom.html",
        )
        assert snap.snapshot_id == "abc-123"
        assert snap.url == "https://example.com"
        assert snap.hostname == "example.com"

    def test_roundtrip_json(self):
        snap = SiteSnapshot(
            snapshot_id="test-id",
            url="https://example.com",
            hostname="example.com",
            title="Test",
            captured_at="2026-06-01T12:00:00",
            semantic_elements=[
                SemanticElement(tag="button", text="Click", selector="button#btn"),
            ],
            layout_elements=[
                LayoutElement(selector="button#btn", x=5, y=10, width=80, height=30, visible=True),
            ],
            screenshot_path="data/captures/test-id/screenshot.png",
            dom_path="data/captures/test-id/dom.html",
        )
        data = json.loads(snap.model_dump_json())
        restored = SiteSnapshot(**data)
        assert restored.snapshot_id == snap.snapshot_id
        assert restored.hostname == "example.com"
        assert len(restored.semantic_elements) == 1
        assert len(restored.layout_elements) == 1
        assert restored.semantic_elements[0].text == "Click"


# ---------------------------------------------------------------------------
# DOM cleaning tests
# ---------------------------------------------------------------------------

class TestCleanDom:
    def test_removes_script(self):
        html = '<html><body><p>Hello</p><script>alert("x")</script></body></html>'
        result = clean_dom(html)
        assert "<script>" not in result
        assert "alert" not in result
        assert "<p>Hello</p>" in result

    def test_removes_style(self):
        html = "<html><head><style>body { color: red; }</style></head><body><h1>Title</h1></body></html>"
        result = clean_dom(html)
        assert "<style>" not in result
        assert "color: red" not in result
        assert "<h1>Title</h1>" in result

    def test_removes_svg(self):
        html = '<html><body><svg><circle r="10"/></svg><p>Text</p></body></html>'
        result = clean_dom(html)
        assert "<svg>" not in result
        assert "circle" not in result
        assert "<p>Text</p>" in result

    def test_removes_noscript(self):
        html = "<html><body><noscript>Enable JS</noscript><div>Content</div></body></html>"
        result = clean_dom(html)
        assert "<noscript>" not in result
        assert "Enable JS" not in result
        assert "<div>Content</div>" in result

    def test_preserves_semantic_structure(self):
        html = """<html><body>
            <header><nav><a href="/">Home</a></nav></header>
            <main><h1>Page Title</h1><p>Paragraph</p></main>
            <footer>Footer</footer>
        </body></html>"""
        result = clean_dom(html)
        assert "<header>" in result
        assert "<nav>" in result
        assert "<main>" in result
        assert "<footer>" in result
        assert "<h1>Page Title</h1>" in result

    def test_nested_removed_tags(self):
        html = "<div><script><script>inner</script></script></div>"
        result = clean_dom(html)
        assert "<script>" not in result
        assert "inner" not in result
        assert "<div>" in result

    def test_empty_input(self):
        assert clean_dom("") == ""

    def test_attributes_preserved(self):
        html = '<a href="https://example.com" class="link">Click</a>'
        result = clean_dom(html)
        assert 'href="https://example.com"' in result
        assert 'class="link"' in result


# ---------------------------------------------------------------------------
# Storage tests
# ---------------------------------------------------------------------------

def _make_snapshot(snapshot_id="snap-001", url="https://example.com", hostname="example.com",
                   title="Example Domain", captured_at="2026-06-20T12:00:00",
                   semantic_elements=None, layout_elements=None):
    """Helper to create a SiteSnapshot with defaults."""
    if semantic_elements is None:
        semantic_elements = [
            SemanticElement(tag="h1", text="Example", selector="h1"),
            SemanticElement(tag="a", text="More info", selector="a#more", role="link"),
        ]
    if layout_elements is None:
        layout_elements = [
            LayoutElement(selector="h1", x=0, y=100, width=300, height=40, visible=True),
        ]
    return SiteSnapshot(
        snapshot_id=snapshot_id,
        url=url,
        hostname=hostname,
        title=title,
        captured_at=captured_at,
        semantic_elements=semantic_elements,
        layout_elements=layout_elements,
        screenshot_path=f"data/captures/{snapshot_id}/screenshot.png",
        dom_path=f"data/captures/{snapshot_id}/dom.html",
    )


class TestCaptureStorage:
    @pytest.fixture
    def storage(self, tmp_path):
        return CaptureStorage(base_dir=str(tmp_path / "captures"))

    @pytest.fixture
    def sample_snapshot(self):
        return _make_snapshot()

    def test_save_and_load(self, storage, sample_snapshot):
        screenshot_bytes = b"\x89PNG\r\n\x1a\nfake_png_data"
        dom_html = "<html><body><h1>Example</h1></body></html>"

        saved = storage.save_snapshot(sample_snapshot, screenshot_bytes, dom_html)

        # Verify files exist
        snap_dir = os.path.join(storage.base_dir, "snap-001")
        assert os.path.isfile(os.path.join(snap_dir, "record.json"))
        assert os.path.isfile(os.path.join(snap_dir, "screenshot.png"))
        assert os.path.isfile(os.path.join(snap_dir, "dom.html"))

        # Verify screenshot content
        with open(os.path.join(snap_dir, "screenshot.png"), "rb") as f:
            assert f.read() == screenshot_bytes

        # Verify DOM content
        with open(os.path.join(snap_dir, "dom.html"), "r", encoding="utf-8") as f:
            assert f.read() == dom_html

        # Load and verify
        loaded = storage.load_snapshot("snap-001")
        assert loaded is not None
        assert loaded.snapshot_id == "snap-001"
        assert loaded.url == "https://example.com"
        assert loaded.hostname == "example.com"
        assert loaded.title == "Example Domain"
        assert len(loaded.semantic_elements) == 2
        assert len(loaded.layout_elements) == 1

    def test_load_nonexistent(self, storage):
        result = storage.load_snapshot("does-not-exist")
        assert result is None

    def test_list_snapshots_empty(self, storage):
        result = storage.list_snapshots()
        assert result == []

    def test_list_snapshots_multiple(self, storage):
        for i, ts in enumerate(["2026-06-01T00:00:00", "2026-06-03T00:00:00", "2026-06-02T00:00:00"]):
            snap = _make_snapshot(
                snapshot_id=f"snap-{i}",
                url=f"https://example{i}.com",
                hostname=f"example{i}.com",
                title=f"Example {i}",
                captured_at=ts,
                semantic_elements=[],
                layout_elements=[],
            )
            storage.save_snapshot(snap, b"png", "<html></html>")

        results = storage.list_snapshots()
        assert len(results) == 3
        # Should be sorted by captured_at descending
        assert results[0].captured_at == "2026-06-03T00:00:00"
        assert results[1].captured_at == "2026-06-02T00:00:00"
        assert results[2].captured_at == "2026-06-01T00:00:00"


# ---------------------------------------------------------------------------
# Analytics tests
# ---------------------------------------------------------------------------

class TestCaptureSummary:
    @pytest.fixture
    def storage(self, tmp_path):
        return CaptureStorage(base_dir=str(tmp_path / "captures"))

    def test_summary_returns_counts_and_sizes(self, storage):
        snap = _make_snapshot()
        dom_html = "<html><body><h1>Hello World</h1></body></html>"
        screenshot_bytes = b"\x89PNG" + b"\x00" * 1000
        storage.save_snapshot(snap, screenshot_bytes, dom_html)

        summary = get_capture_summary(storage, "snap-001")
        assert summary is not None
        assert summary.snapshot_id == "snap-001"
        assert summary.hostname == "example.com"
        assert summary.semantic_count == 2
        assert summary.layout_count == 1
        assert summary.dom_size_bytes > 0
        assert summary.screenshot_size_bytes > 0

    def test_summary_nonexistent(self, storage):
        assert get_capture_summary(storage, "no-such-id") is None


class TestCaptureHealth:
    @pytest.fixture
    def storage(self, tmp_path):
        return CaptureStorage(base_dir=str(tmp_path / "captures"))

    def test_healthy_capture(self, storage):
        elements = [SemanticElement(tag="button", text=f"btn-{i}", selector=f"button:nth-of-type({i})") for i in range(15)]
        layouts = [LayoutElement(selector=f"el-{i}", x=i*10, y=0, width=50, height=30, visible=True) for i in range(20)]
        snap = _make_snapshot(semantic_elements=elements, layout_elements=layouts)
        storage.save_snapshot(snap, b"png", "<html></html>")

        health = get_capture_health(storage, "snap-001")
        assert health is not None
        assert health.semantic_score == 1.0
        assert health.layout_score == 1.0
        assert health.score == 1.0
        assert health.warnings == []

    def test_empty_capture_warns(self, storage):
        snap = _make_snapshot(semantic_elements=[], layout_elements=[])
        storage.save_snapshot(snap, b"png", "<html></html>")

        health = get_capture_health(storage, "snap-001")
        assert health is not None
        assert health.score == 0.0
        assert "No semantic elements captured" in health.warnings
        assert "No layout elements captured" in health.warnings

    def test_truncated_layout_warns(self, storage):
        elements = [SemanticElement(tag="a", text=f"link-{i}", selector=f"a:nth-of-type({i})") for i in range(10)]
        layouts = [LayoutElement(selector=f"el-{i}", x=0, y=0, width=10, height=10, visible=True) for i in range(500)]
        snap = _make_snapshot(semantic_elements=elements, layout_elements=layouts)
        storage.save_snapshot(snap, b"png", "<html></html>")

        health = get_capture_health(storage, "snap-001")
        assert health is not None
        assert "Layout capture truncated at 500 elements" in health.warnings
        assert health.layout_score == 0.7

    def test_nonexistent(self, storage):
        assert get_capture_health(storage, "nope") is None
