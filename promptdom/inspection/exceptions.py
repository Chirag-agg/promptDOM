class BrowserUnavailableError(Exception):
    """Raised when the browser connection cannot be established or is unavailable."""
    pass

class NoActivePageError(Exception):
    """Raised when there is no active page available in the browser context."""
    pass

class PageClosedError(Exception):
    """Raised when the active page has been closed."""
    pass
