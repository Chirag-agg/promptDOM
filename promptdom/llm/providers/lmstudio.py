from .openai_compatible import BaseOpenAICompatibleProvider

class LMStudioProvider(BaseOpenAICompatibleProvider):
    def __init__(self, model_name: str, timeout: int = 30):
        super().__init__(
            base_url="http://localhost:1234/v1",
            model_name=model_name,
            timeout=timeout
        )
