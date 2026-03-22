# AuthCord Python SDK

Official Python SDK for the AuthCord authentication platform.

## Installation

```bash
pip install authcord
```

## Quick Start

```python
from authcord import AuthCordClient

client = AuthCordClient(api_key="ac_your_api_key_here")

# Validate user access
result = client.validate(
    "your_app_id",
    discord_id="123456789012345678",
    hwid="unique_hardware_id"
)

if result.valid:
    print(f"Welcome, {result.user.username}!")
    print(f"Mode: {result.mode}")           # "active" or "grace"
    print(f"Entitlements: {result.entitlements}")
    print(f"Config: {result.config}")
    for product in result.products:
        print(f"  - {product.name} (expires: {product.expires_at})")
else:
    print(f"Access denied: {result.reason}")
```

## Email-Based Validation

AuthCord supports validating users by Discord ID, user ID, or email:

```python
# Validate by email
result = client.validate(
    "your_app_id",
    email="user@example.com",
    hwid="unique_hardware_id"
)

# Validate by custom user ID
result = client.validate(
    "your_app_id",
    user_id="user123",
    hwid="unique_hardware_id"
)

# Validate by Discord ID (original method)
result = client.validate(
    "your_app_id",
    discord_id="123456789012345678",
    hwid="unique_hardware_id"
)
```

## Session-Based Auth (Desktop Apps)

```python
# Create a persistent session (do once after Discord login)
session = client.create_session(
    "your_app_id",
    "unique_hardware_id",
    discord_id="123456789012345678",
    device_name="My Gaming PC"
)

# Save session.session_token locally

# On subsequent launches, validate with token (no Discord ID needed)
result = client.validate_session(
    session_token=saved_token,
    hwid="unique_hardware_id"
)

if result.valid:
    print(f"Device: {result.session_info.device_name}")
    print(f"Last seen: {result.session_info.last_seen}")
```

## Offline Mode

```python
# When online: get an offline token
offline_token = client.get_offline_token(
    "your_app_id",
    discord_id="123456789012345678",
    hwid="unique_hardware_id",
    ttl=24  # Valid for 24 hours
)

# Cache the public key (do once)
pub_key = client.get_public_key(app_id="your_app_id")

# When offline: verify locally (no internet needed)
result = client.verify_offline(
    token=offline_token.token,
    public_key=pub_key.public_key,
    hwid="unique_hardware_id"
)
```

## Features

- User validation with HWID protection
- Session-based auth for desktop apps
- Entitlements and remote config support
- Grace period / soft enforcement modes
- Offline token generation and verification
- Automatic retry logic for network errors
- Type hints throughout

## License

MIT
