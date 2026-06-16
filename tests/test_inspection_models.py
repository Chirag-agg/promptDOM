import pytest
from promptdom.inspection.models import InspectionResponse, DOMSummary, PageHeading, PageButton, PageInput, PageLink, PageSection, InteractiveElement, CompactInspectionResponse

def test_inspection_response_model():
    summary = DOMSummary(
        heading_count=1, button_count=1, input_count=1, link_count=1, section_count=1, visible_text_length=10
    )
    
    response = InspectionResponse(
        url="https://youtube.com/watch?v=123",
        hostname="youtube.com",
        title="Test Video",
        page_type="video",
        dom_fingerprint="abc123hash",
        headings=[PageHeading(text="Hello", level=1, id="h1-id")],
        buttons=[PageButton(text="Click Me", tag="button", id="btn-id", classes="btn-class", aria_label="click")],
        inputs=[PageInput(type="text", placeholder="Search...", name="q", id="search-box")],
        links=[PageLink(text="Home", href="https://youtube.com/")],
        sections=[PageSection(role="main", identifier="main-content", text_preview="Content here")],
        interactive_elements=[InteractiveElement(type="button", text="Click Me")],
        visible_text_sample="Hello World",
        summary=summary
    )
    
    assert response.url == "https://youtube.com/watch?v=123"
    assert response.page_type == "video"
    assert response.dom_fingerprint == "abc123hash"
    assert len(response.buttons) == 1
    assert response.buttons[0].aria_label == "click"

def test_compact_inspection_response_model():
    response = CompactInspectionResponse(
        title="Compact Title",
        page_type="article",
        sections=[PageSection(role="main", identifier="content", text_preview="Article text")],
        visible_text_sample="Article sample"
    )
    
    assert response.title == "Compact Title"
    assert response.page_type == "article"
    assert len(response.sections) == 1
