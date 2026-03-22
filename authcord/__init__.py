"""AuthCord Python SDK - Official client library for AuthCord authentication."""

__version__ = "1.0.0"

from .client import AuthCordClient
from .models import (
    User, Product, File, HwidResult, ValidationResult,
    Session, SessionCreateResult, OfflineToken, PublicKey,
    SessionInfo,
)
from .exceptions import (
    AuthCordError, AuthenticationError, ValidationError,
    APIError, NetworkError, OfflineTokenError, RateLimitError,
)

__all__ = [
    "AuthCordClient",
    "User", "Product", "File", "HwidResult", "ValidationResult",
    "Session", "SessionCreateResult", "OfflineToken", "PublicKey", "SessionInfo",
    "AuthCordError", "AuthenticationError", "ValidationError",
    "APIError", "NetworkError", "OfflineTokenError", "RateLimitError",
]
