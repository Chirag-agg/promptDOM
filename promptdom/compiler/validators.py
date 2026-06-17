from .models import ActionSpec, FeatureSpec

class CompilerValidationError(Exception):
    pass

class FeatureValidator:
    def validate_action(self, action: ActionSpec):
        if hasattr(action, "selector") and action.selector is not None:
            if len(action.selector) > 2000:
                raise CompilerValidationError("Selector exceeds maximum length of 2000 characters")
            if len(action.selector) == 0:
                raise CompilerValidationError("Selector cannot be empty")
                
        if action.action_type == "periodic_task":
            if action.interval_ms < 100:
                raise CompilerValidationError("Periodic task interval too short (min 100ms)")
            if action.interval_ms > 3600000:
                raise CompilerValidationError("Periodic task interval too long (max 1 hour)")
                
        if action.action_type == "text_match_highlight":
            if not action.pattern or len(action.pattern) > 500:
                raise CompilerValidationError("Invalid text match pattern")

    def validate_feature(self, spec: FeatureSpec):
        if not spec.actions:
            raise CompilerValidationError("Feature must contain at least one action")
        for action in spec.actions:
            self.validate_action(action)
