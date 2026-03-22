"""Main AuthCord client class."""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from ._http import HTTPClient
from .models import (
    ValidationResult, User, Product, File, HwidResult,
    SessionCreateResult, Session, OfflineToken, PublicKey,
    SessionInfo,
)
from .offline import verify_offline_token as _verify_offline


def _parse_dt(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, str):
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    return val


class AuthCordClient:
    """Official AuthCord Python SDK client.

    Example::

        client = AuthCordClient(api_key="ac_...")
        result = client.validate("abc", discord_id="123")
        if result.valid:
            print(f"Welcome {result.user.username}!")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://authcord.dev",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self._http = HTTPClient(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=max_retries)

    def validate(
        self,
        app_id: str,
        *,
        discord_id: Optional[str] = None,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        product_id: Optional[str] = None,
        hwid: Optional[str] = None,
        ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_meta: Optional[Dict[str, Any]] = None,
        binary_hash: Optional[str] = None,
        app_version: Optional[str] = None,
    ) -> ValidationResult:
        """Validate a user's access to your app.

        At least one of ``discord_id``, ``user_id``, or ``email`` must be provided.
        """
        if not discord_id and not user_id and not email:
            raise ValueError("At least one of discord_id, user_id, or email is required.")
        body: Dict[str, Any] = {"app_id": app_id}
        if discord_id: body["discord_id"] = discord_id
        if user_id: body["user_id"] = user_id
        if email: body["email"] = email
        if product_id: body["product_id"] = product_id
        if hwid: body["hwid"] = hwid
        if ip: body["ip"] = ip
        if user_agent: body["user_agent"] = user_agent
        if device_meta: body["device_meta"] = device_meta
        if binary_hash: body["binary_hash"] = binary_hash
        if app_version: body["app_version"] = app_version

        r = self._http.post("/api/v1/auth/validate", json=body)
        return self._parse_validation(r)

    def create_session(
        self,
        app_id: str,
        hwid: str,
        *,
        discord_id: Optional[str] = None,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        device_name: Optional[str] = None,
        device_meta: Optional[Dict[str, Any]] = None,
    ) -> SessionCreateResult:
        """Create a persistent device session.

        At least one of ``discord_id``, ``user_id``, or ``email`` must be provided.
        """
        if not discord_id and not user_id and not email:
            raise ValueError("At least one of discord_id, user_id, or email is required.")
        body: Dict[str, Any] = {"app_id": app_id, "hwid": hwid}
        if discord_id: body["discord_id"] = discord_id
        if user_id: body["user_id"] = user_id
        if email: body["email"] = email
        if device_name: body["device_name"] = device_name
        if device_meta: body["device_meta"] = device_meta

        r = self._http.post("/api/v1/auth/sessions/create", json=body)
        return SessionCreateResult(
            success=r["success"],
            session_token=r["session_token"],
            expires_at=_parse_dt(r["expires_at"]) or datetime.now(),
            device_name=r.get("device_name"),
        )

    def validate_session(
        self,
        session_token: str,
        hwid: str,
        product_id: Optional[str] = None,
        device_meta: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """Validate using a session token."""
        body: Dict[str, Any] = {"session_token": session_token, "hwid": hwid}
        if product_id: body["product_id"] = product_id
        if device_meta: body["device_meta"] = device_meta

        r = self._http.post("/api/v1/auth/sessions/validate", json=body)
        return self._parse_validation(r)

    def revoke_session(self, session_token: str) -> bool:
        """Revoke a specific session by token."""
        r = self._http.post("/api/v1/auth/sessions/revoke", json={"session_token": session_token})
        return r.get("success", False)

    def revoke_all_sessions(self, discord_id: str, app_id: str) -> int:
        """Revoke all sessions for a user in an app. Returns count revoked."""
        r = self._http.post("/api/v1/auth/sessions/revoke", json={"discord_id": discord_id, "app_id": app_id})
        return r.get("count", 0)

    def list_sessions(self, discord_id: str, app_id: str) -> List[Session]:
        """List all sessions for a user in an app."""
        r = self._http.get("/api/v1/auth/sessions/list", params={"discord_id": discord_id, "app_id": app_id})
        return [
            Session(
                id=s["id"], device_name=s.get("device_name"), hwid=s["hwid"],
                ip=s.get("ip"), created_at=_parse_dt(s["created_at"]) or datetime.now(),
                last_used_at=_parse_dt(s["last_used_at"]) or datetime.now(),
                expires_at=_parse_dt(s["expires_at"]) or datetime.now(),
                revoked_at=_parse_dt(s.get("revoked_at")), is_active=s.get("is_active", False),
            )
            for s in r.get("sessions", [])
        ]

    def get_offline_token(
        self,
        app_id: str,
        *,
        discord_id: Optional[str] = None,
        user_id: Optional[str] = None,
        email: Optional[str] = None,
        product_id: Optional[str] = None,
        hwid: Optional[str] = None,
        ttl: Optional[int] = None,
    ) -> OfflineToken:
        """Generate a signed offline token.

        At least one of ``discord_id``, ``user_id``, or ``email`` must be provided.
        """
        if not discord_id and not user_id and not email:
            raise ValueError("At least one of discord_id, user_id, or email is required.")
        body: Dict[str, Any] = {"app_id": app_id}
        if discord_id: body["discord_id"] = discord_id
        if user_id: body["user_id"] = user_id
        if email: body["email"] = email
        if product_id: body["product_id"] = product_id
        if hwid: body["hwid"] = hwid
        if ttl: body["ttl"] = ttl

        r = self._http.post("/api/v1/auth/offline-token", json=body)
        return OfflineToken(
            token=r["token"], payload=r["payload"],
            expires_at=_parse_dt(r["expires_at"]) or datetime.now(),
        )

    def get_public_key(self, app_id: str) -> PublicKey:
        """Get the public key for offline token verification."""
        r = self._http.get("/api/v1/auth/offline-token/public-key", params={"app_id": app_id})
        return PublicKey(public_key=r["public_key"], algorithm=r["algorithm"])

    def verify_offline(self, token: str, public_key: str, hwid: Optional[str] = None) -> ValidationResult:
        """Verify an offline token locally (no internet required)."""
        return _verify_offline(token, public_key, hwid)

    def _parse_validation(self, r: Dict[str, Any]) -> ValidationResult:
        if not r.get("valid"):
            return ValidationResult(
                valid=False, reason=r.get("reason"),
                banned=r.get("banned", False), hwid_mismatch=r.get("hwid_mismatch", False),
            )
        user = User(discord_id=r["user"]["discord_id"], username=r["user"]["username"])
        products = [
            Product(
                id=p["id"], name=p["name"], expires_at=_parse_dt(p.get("expires_at")),
                is_lifetime=p.get("is_lifetime", False), hwid_status=p.get("hwid_status"),
            ) for p in r.get("products", [])
        ]
        hwid_results = [
            HwidResult(product_id=h["productId"], product_name=h["productName"], hwid_status=h["hwidStatus"])
            for h in r.get("hwid_results", [])
        ]
        files = [
            File(
                id=f["id"], name=f["name"], filename=f["filename"], size=f["size"],
                description=f.get("description"), version=f.get("version"),
                checksum=f.get("checksum"), stream_only=f.get("stream_only", False),
            ) for f in r.get("files", [])
        ]
        # Parse session info if present (session validate only)
        session_info = None
        if "session" in r:
            s = r["session"]
            session_info = SessionInfo(
                device_name=s.get("device_name"),
                first_seen=_parse_dt(s.get("first_seen")),
                last_seen=_parse_dt(s.get("last_seen")),
                ip=s.get("ip"),
                user_agent=s.get("user_agent"),
            )

        return ValidationResult(
            valid=True, mode=r.get("mode"), user=user, products=products,
            hwid_results=hwid_results, metadata=r.get("metadata"),
            config=r.get("config"), entitlements=r.get("entitlements"),
            files=files, session_info=session_info,
        )

    def close(self) -> None:
        self._http.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
