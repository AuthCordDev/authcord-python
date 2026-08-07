"""Main AuthCord client class."""

from __future__ import annotations
import threading
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from ._http import HTTPClient
from .models import (
    ValidationResult, User, Product, File, HwidResult,
    SessionCreateResult, Session, OfflineToken, PublicKey,
    SessionInfo, HeartbeatResult, HwidComponents,
    PausedProduct, PauseResult, UnpauseResult, ResetHwidResult,
)
from .offline import verify_offline_token as _verify_offline


def collect_hwid_components() -> HwidComponents:
    """Best-effort collector for spoofer-resistant HWID components.

    On Windows: populates ``sid`` (User SID via wmic/whoami fallback),
    ``cpu_id`` (CPUID via wmic), and ``machine_guid`` (registry).

    On non-Windows: returns an empty :class:`HwidComponents`. Cross-
    platform callers should fill the struct themselves with whatever
    stable identifiers their platform exposes, then pass it to
    :meth:`AuthCordClient.validate`.
    """
    import sys
    out = HwidComponents()
    if not sys.platform.startswith("win"):
        return out

    # ── Windows User SID ──
    # Stable across temp HWID spoofers because changing it would break
    # the user's Windows profile.
    try:
        import subprocess
        r = subprocess.run(
            ["whoami", "/user", "/fo", "csv", "/nh"],
            capture_output=True, text=True, timeout=5,
        )
        # Output is e.g. "DESKTOP-XYZ\\charlie","S-1-5-21-...-1001"
        if r.returncode == 0 and r.stdout:
            parts = [p.strip().strip('"') for p in r.stdout.strip().split(",")]
            for part in parts:
                if part.startswith("S-1-5-"):
                    out.sid = part
                    break
    except Exception:
        pass

    # ── Windows MachineGuid ──
    try:
        import winreg  # type: ignore
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Cryptography",
            0,
            winreg.KEY_READ | winreg.KEY_WOW64_64KEY,
        ) as key:
            val, _ = winreg.QueryValueEx(key, "MachineGuid")
            if val:
                out.machine_guid = str(val)
    except Exception:
        pass

    # ── CPU ID ──
    # Use the wmic ProcessorId. Not unique per chip (Intel deprecated PSN
    # in P3) but stable across reboots and spoofers, which is all we need.
    try:
        import subprocess
        r = subprocess.run(
            ["wmic", "cpu", "get", "ProcessorId", "/value"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0:
            for line in r.stdout.splitlines():
                line = line.strip()
                if line.startswith("ProcessorId="):
                    val = line.split("=", 1)[1].strip()
                    if val:
                        out.cpu_id = val
                        break
    except Exception:
        pass

    return out


class HeartbeatLoop:
    """Background heartbeat task. Stop with ``.stop()``."""

    def __init__(self, thread: threading.Thread, stop_event: threading.Event):
        self._thread = thread
        self._stop = stop_event

    def stop(self, *, wait: bool = True, timeout: float = 5.0) -> None:
        self._stop.set()
        if wait:
            self._thread.join(timeout=timeout)

    @property
    def is_running(self) -> bool:
        return self._thread.is_alive() and not self._stop.is_set()


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
        hwid_components: Optional[HwidComponents] = None,
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
        if hwid_components:
            comps = hwid_components.to_dict()
            if comps:
                body["hwid_components"] = comps
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

    def heartbeat(
        self,
        app_id: str,
        *,
        discord_id: Optional[str] = None,
        hwid: Optional[str] = None,
        hwid_components: Optional[HwidComponents] = None,
        session_token: Optional[str] = None,
    ) -> HeartbeatResult:
        """Single heartbeat check — returns whether the user's session is
        still live.

        Pass ``session_token`` (for DeviceSession-based flows) OR
        ``discord_id`` plus EITHER ``hwid`` (legacy) or
        ``hwid_components`` (validates against STABLE/STRICT apps).

        Returns a :class:`HeartbeatResult` with ``valid`` plus a ``reason``
        like ``"terminated"``, ``"banned"``, ``"paused"``, ``"expired"``,
        or ``"hwid_unbound"`` when invalid.
        """
        has_hwid_signal = bool(hwid) or bool(hwid_components and hwid_components.to_dict())
        if not session_token and not (discord_id and has_hwid_signal):
            raise ValueError("Provide session_token, or discord_id with hwid or hwid_components")
        body: Dict[str, Any] = {"app_id": app_id}
        if session_token: body["session_token"] = session_token
        if discord_id: body["discord_id"] = discord_id
        if hwid: body["hwid"] = hwid
        if hwid_components:
            comps = hwid_components.to_dict()
            if comps:
                body["hwid_components"] = comps
        r = self._http.post("/api/v1/auth/heartbeat", json=body)
        return HeartbeatResult(
            valid=bool(r.get("valid")),
            reason=r.get("reason"),
            next_heartbeat_in=int(r.get("next_heartbeat_in") or 10),
        )

    def start_heartbeat(
        self,
        app_id: str,
        on_terminated: Callable[[HeartbeatResult], None],
        *,
        discord_id: Optional[str] = None,
        hwid: Optional[str] = None,
        hwid_components: Optional[HwidComponents] = None,
        session_token: Optional[str] = None,
        interval: Optional[float] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
    ) -> HeartbeatLoop:
        """Start a daemon background thread that polls the heartbeat
        endpoint and fires ``on_terminated`` exactly once when the server
        returns ``valid=False``.

        After ``on_terminated`` fires, the loop stops automatically — your
        app is expected to log the user out and exit / return to login.

        ``interval`` is the seconds between polls. When omitted, the server
        decides via the ``next_heartbeat_in`` field (default 10s). Network
        errors are reported via ``on_error`` and the loop keeps running.
        """
        has_hwid_signal = bool(hwid) or bool(hwid_components and hwid_components.to_dict())
        if not session_token and not (discord_id and has_hwid_signal):
            raise ValueError("Provide session_token, or discord_id with hwid or hwid_components")

        stop_event = threading.Event()

        def _loop() -> None:
            wait_seconds = float(interval) if interval is not None else 10.0
            while not stop_event.is_set():
                if stop_event.wait(timeout=wait_seconds):
                    return  # stopped during sleep
                try:
                    result = self.heartbeat(
                        app_id,
                        discord_id=discord_id,
                        hwid=hwid,
                        hwid_components=hwid_components,
                        session_token=session_token,
                    )
                except Exception as exc:  # network error, rate limit, etc.
                    if on_error is not None:
                        try:
                            on_error(exc)
                        except Exception:
                            pass
                    continue
                if not result.valid:
                    try:
                        on_terminated(result)
                    finally:
                        return
                # Honour server-suggested interval when caller didn't pin it
                if interval is None:
                    wait_seconds = max(1.0, float(result.next_heartbeat_in))

        thread = threading.Thread(target=_loop, name="authcord-heartbeat", daemon=True)
        thread.start()
        return HeartbeatLoop(thread=thread, stop_event=stop_event)

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

    # ------------------------------------------------------------------
    # Admin operations — server-side only, require a FULL API key.
    # ------------------------------------------------------------------

    def pause_product(
        self,
        app_id: str,
        discord_id: str,
        days: int,
        *,
        product_id: Optional[str] = None,
        reason: Optional[str] = None,
        paused_by: Optional[str] = None,
    ) -> PauseResult:
        """Pause (freeze the expiry clock) one product — or every product the
        user owns on the app when ``product_id`` is omitted — for ``days`` days.

        **Server-side only. Requires a FULL API key** (a CLIENT key gets 403).

        Does not raise on the expected 404 cases (app/user/product not found,
        user owns nothing) or the 409 already-paused case — inspect
        ``result.success``, ``result.error`` and ``result.reason``. Auth (401),
        rate-limit (429), network and server (5xx) errors still raise.
        """
        body: Dict[str, Any] = {"app_id": app_id, "discord_id": discord_id, "days": days}
        if product_id: body["product_id"] = product_id
        if reason is not None: body["reason"] = reason
        if paused_by is not None: body["paused_by"] = paused_by
        status, data = self._http.request_raw("POST", "/api/v1/products/pause", json=body)
        return PauseResult(
            success=bool(data.get("success", 200 <= status < 300)),
            status=status,
            paused=[PausedProduct(**{k: p.get(k) for k in ("product_id", "paused_at", "pause_ends_at", "frozen_expires_at")})
                    for p in (data.get("paused") or [])],
            error=data.get("error"),
            reason=data.get("reason"),
            message=data.get("message"),
        )

    def unpause_product(
        self,
        app_id: str,
        discord_id: str,
        *,
        product_id: Optional[str] = None,
    ) -> UnpauseResult:
        """Unpause one product — or every paused product on the app when
        ``product_id`` is omitted. Idempotent. **Requires a FULL API key.**
        Same error semantics as :meth:`pause_product`."""
        body: Dict[str, Any] = {"app_id": app_id, "discord_id": discord_id}
        if product_id: body["product_id"] = product_id
        status, data = self._http.request_raw("POST", "/api/v1/products/unpause", json=body)
        return UnpauseResult(
            success=bool(data.get("success", 200 <= status < 300)),
            status=status,
            unpaused=list(data.get("unpaused") or []),
            error=data.get("error"),
            reason=data.get("reason"),
        )

    def reset_hwid(
        self,
        app_id: str,
        discord_id: str,
        *,
        product_id: Optional[str] = None,
        hwid: Optional[str] = None,
        bypass_cooldown: bool = False,
        reason: Optional[str] = None,
    ) -> ResetHwidResult:
        """Clear the HWID binding(s) for a user on one product — or every
        product the user owns on the app when ``product_id`` is omitted — so
        they can re-bind on a new machine. Idempotent for unbound products.

        The app's HWID reset cooldown applies (same rule as dashboard and
        self-service resets): a product still inside its cooldown is skipped
        with ``on_cooldown: true``, and the call returns HTTP 409
        ``cooldown_active`` if every targeted product was blocked. Pass
        ``bypass_cooldown=True`` for an explicit admin override.

        Pass ``hwid`` (requires ``product_id``) to clear a single device slot
        instead of all of them. ``reason`` is stored in the reset log.

        **Requires a FULL API key**; scoped keys need the ``devices:reset``
        scope. Resets are attributed to the calling key in the reset and
        audit logs. Same error semantics as :meth:`pause_product`."""
        body: Dict[str, Any] = {"app_id": app_id, "discord_id": discord_id}
        if product_id: body["product_id"] = product_id
        if hwid: body["hwid"] = hwid
        if bypass_cooldown: body["bypass_cooldown"] = True
        if reason: body["reason"] = reason
        status, data = self._http.request_raw("POST", "/api/v1/products/reset-hwid", json=body)
        return ResetHwidResult(
            success=bool(data.get("success", 200 <= status < 300)),
            status=status,
            reset=list(data.get("reset") or []),
            error=data.get("error"),
            reason=data.get("reason"),
        )

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
        if ttl is not None: body["ttl"] = ttl

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
