class ProviderConnectionError(Exception):
    """Raised when the LLM provider cannot be reached."""
    pass

class ProviderTimeoutError(Exception):
    """Raised when the LLM provider takes too long to respond."""
    pass

class ProviderResponseError(Exception):
    """Raised when the LLM provider returns an HTTP error or malformed response."""
    pass

class ProviderValidationError(Exception):
    """Raised when the LLM provider output cannot be parsed into the requested schema."""
    pass
