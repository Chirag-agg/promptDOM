import base64
from ..llm.base import BaseLLMProvider
from .models import GoalAnalysis, EvaluationResult

class EvaluatorService:
    def __init__(self, vision_llm: BaseLLMProvider):
        self.llm = vision_llm
        self.system_prompt = """You are an expert QA visual evaluator.
Your job is to look at a screenshot of a web page after a transformation and determine if a requested transformation was successful based on the defined goals.

You must look closely at the image to see if the goals were met.
If the goal is to hide or remove an element, check carefully if that element is still visible anywhere on the screen in the image.
If it is still visible, the transformation FAILED (`worked` = false), and you must list the logical name of the element (e.g. "Shorts shelf") in `unresolved_targets`.

If the goal is restyling, check if the styles reflect the requested design.
Respond ONLY in valid JSON matching the requested schema.
"""

    async def evaluate(self, prompt: str, goal: GoalAnalysis, before_screenshot_path: str, after_screenshot_path: str) -> EvaluationResult:
        
        # Load images as base64
        with open(before_screenshot_path, "rb") as f:
            before_b64 = base64.b64encode(f.read()).decode("utf-8")
        with open(after_screenshot_path, "rb") as f:
            after_b64 = base64.b64encode(f.read()).decode("utf-8")
            
        user_prompt = f"""Evaluate this transformation.
Original Prompt: "{prompt}"

Primary Goal: {goal.primary_goal.value}
Secondary Goals: {[g.value for g in goal.secondary_goals]}

This image is AFTER the transformation.

Did the transformation succeed? Look at the image carefully. If elements were supposed to be removed but are still there, it failed.
"""
        return await self.llm.generate_multimodal_structured(
            prompt=user_prompt,
            images_base64=[after_b64],
            schema=EvaluationResult,
            system_prompt=self.system_prompt,
            temperature=0.0
        )
