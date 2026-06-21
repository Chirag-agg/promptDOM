from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Annotated, Union

class LayoutStrategy(BaseModel):
    primary_layout: str = Field(description="The primary layout structure (e.g. 'single_column_feed', 'grid', 'sidebar_and_content')")
    navigation_position: str = Field(description="Where navigation should be moved (e.g. 'left_sidebar', 'top_bar', 'hidden')")
    content_density: str = Field(description="Desired content density (e.g. 'high', 'compact', 'spacious')")

class ContentStrategy(BaseModel):
    remove: List[str] = Field(description="List of logical elements or sections to completely remove (e.g. ['Shorts', 'Comments'])")
    prioritize: List[str] = Field(description="List of logical elements to make more prominent (e.g. ['Videos', 'Search'])")

class VisualStrategy(BaseModel):
    theme: str = Field(description="The visual theme (e.g. 'minimal_dark', 'high_contrast', 'clean_white')")
    spacing: str = Field(description="Spacing strategy (e.g. 'compact', 'generous_padding')")
    card_style: str = Field(description="Card styling strategy (e.g. 'flat', 'elevated_shadows', 'borders_only')")

class RemoveChange(BaseModel):
    type: Literal["REMOVE"]
    target: str = Field(description="The logical element or component to remove")

class MoveChange(BaseModel):
    type: Literal["MOVE"]
    target: str = Field(description="The logical element to move")
    destination: str = Field(description="Where the element should be moved to")

class RestyleChange(BaseModel):
    type: Literal["RESTYLE"]
    target: str = Field(description="The logical element to restyle")
    style_goal: str = Field(description="The visual outcome desired (e.g., 'Make it look like a floating card')")

class AddChange(BaseModel):
    type: Literal["ADD"]
    target: str = Field(description="The logical element to add or inject")
    description: str = Field(description="Description of what to add")

class PrioritizeChange(BaseModel):
    type: Literal["PRIORITIZE"]
    target: str = Field(description="The logical element to prioritize")
    description: str = Field(description="Description of how to prioritize it")

DesignChange = Annotated[
    Union[
        RemoveChange,
        MoveChange,
        RestyleChange,
        AddChange,
        PrioritizeChange,
    ],
    Field(discriminator="type")
]

class DesignPlan(BaseModel):
    goal: str = Field(description="The high-level goal of this redesign")
    layout_strategy: LayoutStrategy
    content_strategy: ContentStrategy
    visual_strategy: VisualStrategy
    changes: List[DesignChange] = Field(default_factory=list, description="Explicit, executable structural changes required to achieve the plan")
    confidence: float = Field(description="Confidence from 0.0 to 1.0 that this redesign plan is viable")
    reasoning: str = Field(description="Brief explanation of why these design choices were made")
