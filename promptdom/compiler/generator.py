from .ast import FeatureAST, ActionAST
from .templates import TemplateRegistry

class JavascriptGenerator:
    @staticmethod
    def _generate_action(ast: ActionAST) -> str:
        template = TemplateRegistry.get_template(ast.action_type)
        
        params = ast.parameters.copy()
        params["action_id"] = ast.action_id
        if ast.selector is not None:
            params["selector"] = ast.selector
            
        # Escape string parameters (including selector)
        for k, v in params.items():
            if isinstance(v, str):
                params[k] = v.replace('\\', '\\\\').replace('`', '\\`')
                
        return template.format(**params)

    @staticmethod
    def generate(ast: FeatureAST) -> str:
        blocks = []
        for action in ast.actions:
            blocks.append(JavascriptGenerator._generate_action(action))
            
        # Combine all action blocks into one feature script
        combined_script = "\n".join(blocks)
        
        return combined_script
