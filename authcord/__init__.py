"""AuthCord Python SDK - Official client library for AuthCord authentication."""

__version__ = "1.3.0"

from .client import AuthCordClient, HeartbeatLoop, collect_hwid_components
from .models import (
    User, Product, File, HwidResult, ValidationResult,
    Session, SessionCreateResult, OfflineToken, PublicKey,
    SessionInfo, HeartbeatResult, HwidComponents,
    PausedProduct, PauseResult, UnpauseResult, ResetHwidResult,
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
    "PausedProduct", "PauseResult", "UnpauseResult", "ResetHwidResult",
    "AuthCordError", "AuthenticationError", "ValidationError",
    "APIError", "NetworkError", "OfflineTokenError", "RateLimitError",
]
