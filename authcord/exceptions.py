"""Custom exceptions for AuthCord SDK."""


class AuthCordError(Exception):
    """Base exception for all AuthCord errors."""
    pass


class AuthenticationError(AuthCordError):
    """Raised when API key authentication fails."""
    def __init__(self, message: str = "Invalid API key"):
        self.message = message
        super().__init__(self.message)


class ValidationError(AuthCordError):
    """Raised when user validation fails."""
    def __init__(self, message: str, reason: str = ""):
        self.message = message
        self.reason = reason
        super().__init__(self.message)


class APIError(AuthCordError):
    """Raised when API request fails."""
    def __init__(self, message: str, status_code: int = 0):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NetworkError(AuthCordError):
    """Raised when network request fails."""
    def __init__(self, message: str = "Network request failed"):
        self.message = message
        super().__init__(self.message)


class OfflineTokenError(AuthCordError):
    """Raised when offline token operations fail."""
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message, status_code=429)
