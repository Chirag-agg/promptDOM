from typing import List
from .base import BasePlanner
from .models import PlannerContext, PlannerResult, ActionPlan

class RulePlanner(BasePlanner):
    def __init__(self):
        self.action_keywords = {
            "hide": ["hide", "remove", "block", "disable"],
            "show": ["show", "display", "enable", "unhide", "unblock"],
            "highlight": ["highlight", "emphasize", "mark", "spotlight"],
            "unhighlight": ["unhighlight", "remove highlight", "clear highlight"]
        }

        self.target_keywords = {
            "youtube_shorts": ["youtube shorts", "shorts", "reels"],
            "comments": ["comments", "comment section"],
            "sidebar": ["sidebar", "side panel", "secondary"]
        }

    async def plan(self, context: PlannerContext) -> PlannerResult:
        prompt_lower = context.prompt.lower().strip()
        
        matched_action = None
        all_action_keywords = []
        for act, keywords in self.action_keywords.items():
            for kw in keywords:
                all_action_keywords.append((kw, act))
        all_action_keywords.sort(key=lambda x: len(x[0]), reverse=True)
        
        for keyword, act in all_action_keywords:
            if keyword in prompt_lower:
                matched_action = act
                break
                
        if not matched_action:
            return PlannerResult(plans=[])
            
        matched_targets = []
        all_target_keywords = []
        for tgt, keywords in self.target_keywords.items():
            for kw in keywords:
                all_target_keywords.append((kw, tgt))
        all_target_keywords.sort(key=lambda x: len(x[0]), reverse=True)
        
        # Track which part of the string matched to allow multi-target
        for keyword, tgt in all_target_keywords:
            if keyword in prompt_lower:
                if tgt not in matched_targets:
                    matched_targets.append(tgt)
                    
        # If no target matched, create an unknown target
        if not matched_targets:
            matched_targets.append("unknown")

        plans = []
        for tgt in matched_targets:
            confidence = 0.5
            reasoning = "Matched keywords but target not found in context."
            target_type = "unknown"
            
            if tgt == "unknown":
                confidence = 0.2
                reasoning = "Target could not be identified."
            elif context.page_context:
                sections = context.page_context.sections
                found_in_context = False
                
                if tgt == "comments":
                    if any("comment" in s.identifier.lower() or "comment" in s.role.lower() for s in sections) or \
                       "comment" in context.page_context.visible_text_sample.lower():
                        found_in_context = True
                        target_type = "section"
                elif tgt == "sidebar":
                    if any("secondary" in s.identifier.lower() or "sidebar" in s.identifier.lower() or "aside" in s.role.lower() for s in sections):
                        found_in_context = True
                        target_type = "section"
                elif tgt == "youtube_shorts":
                    if "shorts" in context.page_context.visible_text_sample.lower() or \
                       any("shorts" in s.identifier.lower() for s in sections):
                        found_in_context = True
                        target_type = "section"
                        
                if found_in_context:
                    confidence = 0.95
                    reasoning = f"Matched '{tgt}' in page context."
            
            plans.append(ActionPlan(
                action=matched_action,
                target=tgt,
                target_type=target_type,
                confidence=confidence,
                reasoning=reasoning
            ))
            
            if len(plans) >= 5:
                break
                
        return PlannerResult(plans=plans)
