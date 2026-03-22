"""Offline token verification utilities."""

from __future__ import annotations
import json
import base64
from datetime import datetime
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.exceptions import InvalidSignature

from .exceptions import OfflineTokenError
from .models import ValidationResult, User, Product


def verify_offline_token(
    token: str,
    public_key: str,
    hwid: Optional[str] = None,
) -> ValidationResult:
    """Verify an offline token locally using the app's public key."""
    try:
        token_bytes = base64.b64decode(token)
        token_data = json.loads(token_bytes)
        payload = token_data["payload"]
        signature = token_data["signature"]
    except (KeyError, json.JSONDecodeError, Exception) as e:
        raise OfflineTokenError(f"Invalid token format: {e}")

    # Verify Ed25519 signature
    try:
        pub_key_bytes = base64.b64decode(public_key)
        pub_key = load_der_public_key(pub_key_bytes)
        if not isinstance(pub_key, Ed25519PublicKey):
            raise OfflineTokenError("Invalid public key type")
        payload_bytes = json.dumps(payload).encode()
        sig_bytes = base64.b64decode(signature)
        pub_key.verify(sig_bytes, payload_bytes)
    except InvalidSignature:
        raise OfflineTokenError("Token signature verification failed")
    except OfflineTokenError:
        raise
    except Exception as e:
        raise OfflineTokenError(f"Signature verification error: {e}")

    # Check expiration
    expires_at = payload.get("expires_at")
    if expires_at and datetime.now().timestamp() > expires_at:
        raise OfflineTokenError("Token has expired")

    # Validate HWID
    token_hwid = payload.get("hwid")
    if hwid and token_hwid and hwid != token_hwid:
        return ValidationResult(valid=False, reason="Hardware ID mismatch", hwid_mismatch=True)

    user = User(discord_id=payload["discord_id"], username=payload.get("username", "Unknown"))
    products = [
        Product(id=pid, name="", expires_at=datetime.fromtimestamp(expires_at) if expires_at else None, is_lifetime=expires_at is None)
        for pid in payload.get("product_ids", [])
    ]

    return ValidationResult(valid=True, user=user, products=products)
