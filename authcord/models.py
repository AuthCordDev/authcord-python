"""Response models for dAuthX API."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class User:
    discord_id: str
    username: str


@dataclass
class Product:
    id: str
    name: str
    expires_at: Optional[datetime] = None
    is_lifetime: bool = False
    hwid_status: Optional[str] = None


@dataclass
class File:
    id: str
    name: str
    filename: str
    size: int
    description: Optional[str] = None
    version: Optional[str] = None
    checksum: Optional[str] = None
    stream_only: bool = False


@dataclass
class HwidResult:
    product_id: str
    product_name: str
    hwid_status: str


@dataclass
class SessionInfo:
    """Device session context (only in session validate responses)."""
    device_name: Optional[str] = None
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class ValidationResult:
    valid: bool
    mode: Optional[str] = None  # "active" | "grace"
    user: Optional[User] = None
    products: Optional[List[Product]] = None
    hwid_results: Optional[List[HwidResult]] = None
    metadata: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, Any]] = None
    entitlements: Optional[Dict[str, Any]] = None
    files: Optional[List[File]] = None
    session_info: Optional[SessionInfo] = None
    reason: Optional[str] = None
    banned: bool = False
    hwid_mismatch: bool = False


@dataclass
class SessionCreateResult:
    success: bool
    session_token: str
    expires_at: datetime
    device_name: Optional[str] = None


@dataclass
class Session:
    id: str
    device_name: Optional[str]
    hwid: str
    ip: Optional[str]
    created_at: datetime
    last_used_at: datetime
    expires_at: datetime
    revoked_at: Optional[datetime]
    is_active: bool


@dataclass
class OfflineToken:
    token: str
    payload: Dict[str, Any]
    expires_at: datetime


@dataclass
class PublicKey:
    public_key: str
    algorithm: str


@dataclass
class HwidComponents:
    """Structured HWID components the SDK can send alongside (or instead of)
    a single opaque ``hwid`` string. The server hashes a subset of these
    — controlled by the app's HWID Strategy in the dashboard — into the
    canonical HWID used for slot matching.

    Typical temp HWID spoofers (used by cheaters to evade FiveM-style
    bans) change SMBIOS UUID, disk serial, MAC, and MachineGuid — but
    NOT the Windows User SID or CPUID. Apps set to ``STABLE`` hash only
    (sid + cpu_id), so users stay bound across spoofs.
    """
    sid: Optional[str] = None           # Windows User SID — survives temp spoofers
    cpu_id: Optional[str] = None        # CPUID signature — silicon
    machine_guid: Optional[str] = None  # HKLM\\SOFTWARE\\Microsoft\\Cryptography\\MachineGuid
    mac: Optional[str] = None           # primary NIC MAC
    disk: Optional[str] = None          # boot disk serial

    def to_dict(self) -> Dict[str, str]:
        """Return only the fields that are set, lowercase keys ready to
        send as the request body's ``hwid_components`` object."""
        return {k: v for k, v in {
            "sid": self.sid,
            "cpu_id": self.cpu_id,
            "machine_guid": self.machine_guid,
            "mac": self.mac,
            "disk": self.disk,
        }.items() if v}


@dataclass
class HeartbeatResult:
    """Result of a heartbeat check.

    ``valid`` is False when the session has been terminated by an admin, the
    user has been banned/paused, the product expired, or the HWID was
    unbound. ``reason`` carries a machine-readable code so the client can
    branch on it (e.g. ``"terminated"`` vs ``"banned"`` vs ``"expired"``).

    ``next_heartbeat_in`` is server-controlled: when ``valid`` is True it
    defaults to 10s, but the server may bump it during incidents or for
    rate-limited clients. The auto-heartbeat loop honours this hint.
    """
    valid: bool
    reason: Optional[str]
    next_heartbeat_in: int = 10
