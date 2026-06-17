from promptdom.compiler.compiler import FeatureCompiler
from promptdom.compiler.models import FeatureSpec, HideElementAction, TextMatchHighlightAction
import pytest

def test_compiler_success():
    compiler = FeatureCompiler()
    spec = FeatureSpec(name="Hide Comments", actions=[HideElementAction(selector="#comments")])
    
    compiled = compiler.compile(spec)
    
    assert compiled.javascript is not None
    assert "document.querySelectorAll(`#comments`)" in compiled.javascript
    assert compiled.compiler_version == "1.0"
    assert compiled.ast.actions[0].action_type == "hide_element"
    assert compiled.ast.actions[0].selector == "#comments"

def test_compiler_escapes():
    compiler = FeatureCompiler()
    # Selector with backticks which would break js template strings
    spec = FeatureSpec(name="Hide", actions=[HideElementAction(selector="div[data-val=`foo`]")])
    
    compiled = compiler.compile(spec)
    
    assert "\\`foo\\`" in compiled.javascript

def test_compiler_text_match():
    compiler = FeatureCompiler()
    spec = FeatureSpec(name="Match AI", actions=[TextMatchHighlightAction(selector="p", pattern="artificial intelligence")])
    
    compiled = compiler.compile(spec)
    assert "artificial intelligence" in compiled.javascript
    assert compiled.ast.actions[0].parameters["pattern"] == "artificial intelligence"
