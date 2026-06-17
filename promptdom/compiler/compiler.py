from .models import FeatureSpec, CompiledFeature
from .ast import FeatureAST, ActionAST
from .validators import FeatureValidator
from .generator import JavascriptGenerator

class FeatureCompiler:
    def __init__(self):
        self.validator = FeatureValidator()
        self.generator = JavascriptGenerator()
        
    def compile(self, spec: FeatureSpec) -> CompiledFeature:
        self.validator.validate_feature(spec)
        # Generate AST
        ast = FeatureAST(
            name=spec.name,
            actions=[]
        )
        
        for action in spec.actions:
            action_params = action.model_dump()
            action_type = action_params.pop("action_type")
            action_id = action_params.pop("action_id", "unknown")
            
            # The rest are parameters
            selector = action_params.pop("selector", None)
            
            ast.actions.append(ActionAST(
                action_id=action_id,
                action_type=action_type,
                selector=selector,
                parameters=action_params
            ))
            
        # Generate Code
        javascript = self.generator.generate(ast)
        
        return CompiledFeature(
            javascript=javascript,
            source_spec=spec,
            ast=ast,
            compiler_version="1.0"
        )
