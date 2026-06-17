from promptdom.compiler.compiler import FeatureCompiler
from promptdom.compiler.models import FeatureSpec, NotifyAction, ObserveElementAction

def test_multi_action_compilation():
    compiler = FeatureCompiler()
    
    spec = FeatureSpec(
        name="Test Compose",
        actions=[
            ObserveElementAction(selector="#target", event="ELEMENT_ADDED"),
            NotifyAction(title="Found it", message="Element appeared!")
        ]
    )
    
    compiled = compiler.compile(spec)
    
    # Verify multiple actions are present
    assert "MutationObserver" in compiled.javascript
    assert "Notification.permission" in compiled.javascript
    
    # Verify AST structure
    assert len(compiled.ast.actions) == 2
    assert compiled.ast.actions[0].action_type == "observe_element"
    assert compiled.ast.actions[1].action_type == "notify"
    
    # Verify parameters are correctly passed
    assert compiled.ast.actions[0].parameters["event"] == "ELEMENT_ADDED"
    assert compiled.ast.actions[1].parameters["title"] == "Found it"
