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
