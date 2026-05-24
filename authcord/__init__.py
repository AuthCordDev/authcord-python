"""AuthCord Python SDK - Official client library for AuthCord authentication."""

__version__ = "1.1.0"

from .client import AuthCordClient, HeartbeatLoop
from .models import (
    User, Product, File, HwidResult, ValidationResult,
    Session, SessionCreateResult, OfflineToken, PublicKey,
    SessionInfo, HeartbeatResult,
)
from .exceptions import (
    AuthCordError, AuthenticationError, ValidationError,
    APIError, NetworkError, OfflineTokenError, RateLimitError,
)

__all__ = [
    "AuthCordClient", "HeartbeatLoop",
    "User", "Product", "File", "HwidResult", "ValidationResult",
    "Session", "SessionCreateResult", "OfflineToken", "PublicKey", "SessionInfo",
    "HeartbeatResult",
    "AuthCordError", "AuthenticationError", "ValidationError",
    "APIError", "NetworkError", "OfflineTokenError", "RateLimitError",
]
