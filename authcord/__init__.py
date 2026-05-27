"""AuthCord Python SDK - Official client library for AuthCord authentication."""

__version__ = "1.2.0"

from .client import AuthCordClient, HeartbeatLoop, collect_hwid_components
from .models import (
    User, Product, File, HwidResult, ValidationResult,
    Session, SessionCreateResult, OfflineToken, PublicKey,
    SessionInfo, HeartbeatResult, HwidComponents,
)
from .exceptions import (
    AuthCordError, AuthenticationError, ValidationError,
    APIError, NetworkError, OfflineTokenError, RateLimitError,
)

__all__ = [
    "AuthCordClient", "HeartbeatLoop", "collect_hwid_components",
    "User", "Product", "File", "HwidResult", "ValidationResult",
    "Session", "SessionCreateResult", "OfflineToken", "PublicKey", "SessionInfo",
    "HeartbeatResult", "HwidComponents",
    "AuthCordError", "AuthenticationError", "ValidationError",
    "APIError", "NetworkError", "OfflineTokenError", "RateLimitError",
]
