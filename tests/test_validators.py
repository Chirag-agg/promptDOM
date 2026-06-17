import pytest
from promptdom.compiler.models import HideElementAction, PeriodicTaskAction, TextMatchHighlightAction, FeatureSpec
from promptdom.compiler.validators import FeatureValidator, CompilerValidationError

def test_valid_specs():
    validator = FeatureValidator()
    
    spec1 = FeatureSpec(name="Hide", actions=[HideElementAction(selector="#x")])
    validator.validate_feature(spec1)
    
    spec2 = FeatureSpec(name="Task", actions=[PeriodicTaskAction(interval_ms=1000, operation="scan_comments")])
    validator.validate_feature(spec2)
    
def test_invalid_selector():
    validator = FeatureValidator()
    with pytest.raises(CompilerValidationError):
        validator.validate_action(HideElementAction(selector=""))
        
    with pytest.raises(CompilerValidationError):
        validator.validate_action(HideElementAction(selector="a" * 3000))
        
def test_invalid_interval():
    validator = FeatureValidator()
    with pytest.raises(CompilerValidationError):
        validator.validate_action(PeriodicTaskAction(interval_ms=50, operation="scan_comments"))
        
    with pytest.raises(CompilerValidationError):
        validator.validate_action(PeriodicTaskAction(interval_ms=5000000, operation="scan_comments"))

def test_invalid_pattern():
    validator = FeatureValidator()
    with pytest.raises(CompilerValidationError):
        validator.validate_action(TextMatchHighlightAction(selector="#x", pattern=""))
