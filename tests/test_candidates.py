import pytest
from promptdom.inspection.models import ResolutionInspectionResponse, PageHeading, PageButton, PageSection
from promptdom.resolution.candidates import CandidateBuilder

def test_candidate_builder():
    inspection = ResolutionInspectionResponse(
        dom_fingerprint="test1234",
        headings=[
            PageHeading(text="Welcome", level=1, id="main-heading", classes="text-xl", aria_label="", data_testid="", css_path="h1#main-heading")
        ],
        buttons=[
            PageButton(text="Submit", tag="button", id="", classes="btn-primary", aria_label="Submit Form", data_testid="submit-btn", css_path="")
        ],
        inputs=[],
        links=[],
        sections=[
            PageSection(role="main", identifier="content", text_preview="Article content", id="", classes="main-container", aria_label="", data_testid="", tag="main", css_path="")
        ],
        interactive_elements=[]
    )
    
    builder = CandidateBuilder()
    candidates = builder.build(inspection)
    
    assert len(candidates) == 3
    
    heading_c = next(c for c in candidates if c.target_type == "heading")
    assert heading_c.selector == "#main-heading"
    
    button_c = next(c for c in candidates if c.target_type == "button")
    # data-testid has priority over aria-label and classes
    assert button_c.selector == '[data-testid="submit-btn"]'
    
    section_c = next(c for c in candidates if c.target_type == "section")
    # No id, data_testid, aria_label, or css_path. Falls back to default_tag + class
    assert section_c.selector == "main.main-container"
