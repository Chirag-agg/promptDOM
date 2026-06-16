from pydantic import BaseModel
from typing import List

class PageHeading(BaseModel):
    text: str
    level: int
    id: str = ""
    classes: str = ""
    aria_label: str = ""
    data_testid: str = ""
    css_path: str = ""

class PageButton(BaseModel):
    text: str
    tag: str
    id: str = ""
    classes: str = ""
    aria_label: str = ""
    data_testid: str = ""
    css_path: str = ""

class PageInput(BaseModel):
    type: str
    placeholder: str = ""
    name: str = ""
    id: str = ""
    classes: str = ""
    aria_label: str = ""
    data_testid: str = ""
    css_path: str = ""

class PageLink(BaseModel):
    text: str
    href: str
    id: str = ""
    classes: str = ""
    aria_label: str = ""
    data_testid: str = ""
    css_path: str = ""

class PageSection(BaseModel):
    role: str
    identifier: str
    text_preview: str = ""
    id: str = ""
    classes: str = ""
    aria_label: str = ""
    data_testid: str = ""
    css_path: str = ""
    tag: str = ""

class InteractiveElement(BaseModel):
    type: str
    text: str
    id: str = ""
    classes: str = ""
    aria_label: str = ""
    data_testid: str = ""
    css_path: str = ""

class DOMSummary(BaseModel):
    heading_count: int
    button_count: int
    input_count: int
    link_count: int
    section_count: int
    visible_text_length: int

class InspectionResponse(BaseModel):
    url: str
    hostname: str
    title: str
    page_type: str
    dom_fingerprint: str
    headings: List[PageHeading]
    buttons: List[PageButton]
    inputs: List[PageInput]
    links: List[PageLink]
    sections: List[PageSection]
    interactive_elements: List[InteractiveElement]
    visible_text_sample: str
    summary: DOMSummary

class CompactInspectionResponse(BaseModel):
    title: str
    page_type: str
    sections: List[PageSection]
    visible_text_sample: str

class ResolutionInspectionResponse(BaseModel):
    dom_fingerprint: str
    headings: List[PageHeading]
    buttons: List[PageButton]
    inputs: List[PageInput]
    links: List[PageLink]
    sections: List[PageSection]
    interactive_elements: List[InteractiveElement]
