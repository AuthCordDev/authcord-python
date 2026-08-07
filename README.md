# AuthCord Python SDK

> [AuthCord](https://authcord.dev) - Sell, authenticate, and manage your software. All in one place. Replace your auth system, payment platform, and Discord bots with a single dashboard.

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

## Real-time Session Kick (Heartbeat)

After `validate()` succeeds, run a background heartbeat so an admin clicking **Terminate** in the dashboard takes effect within ~10 seconds instead of waiting for the user's next manual validate.

```python
def on_terminated(hb):
    print(f"Session ended: {hb.reason}")  # "terminated", "banned", "expired", ...
    # Tear down: close the app, redirect to login, clear in-memory secrets, etc.
    sys.exit(0)

loop = client.start_heartbeat(
    app_id="your_app_id",
    discord_id="123456789012345678",
    hwid="unique_hardware_id",
    on_terminated=on_terminated,
    # on_error=lambda e: ...,    # optional; loop keeps running on transient errors
    # interval=10,                # optional; otherwise the server controls cadence
)

# ... your app does its thing ...
loop.stop()   # clean shutdown on normal sign-out
```

For a DeviceSession-based flow, pass `session_token=...` instead of `discord_id` + `hwid`. Full runnable example in `examples/heartbeat_realtime.py`.

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
- **Real-time session kick** via background heartbeat (~10s detection of admin Terminate)
- Entitlements and remote config support
- Grace period / soft enforcement modes
- Offline token generation and verification
- Automatic retry logic for network errors
- Type hints throughout

## Admin operations (server-side, FULL key only)

`pause_product`, `unpause_product` and `reset_hwid` mutate user state and
require a **FULL** API key (a CLIENT key is rejected with 403). They do **not**
raise on the expected "not found" cases — inspect `.success`, `.error` (machine
code) and `.reason` (human string). Omit `product_id` to apply to every product
the user owns on the app.

`reset_hwid` respects the app's HWID reset cooldown (products still inside it
are skipped with `on_cooldown: true`; the call returns 409 `cooldown_active`
when every target was blocked). Pass `bypass_cooldown=True` for an admin
override, `hwid=` to clear one device slot, and `reason=` for the reset log.
Scoped API keys need the `devices:reset` scope; resets are attributed to the
calling key in the reset and audit logs.

```python
res = client.pause_product(
    "app_id", "discord_id", days=7,
    reason="chargeback hold", paused_by="discord:999",
)
if res.success:
    print("Paused:", res.paused)
elif res.error == "user_not_found":
    print("Not on AuthCord yet:", res.reason)  # pre-cutover case
else:
    print(f"{res.status} {res.error}: {res.reason}")

client.unpause_product("app_id", "discord_id")  # all products
client.reset_hwid("app_id", "discord_id")        # cooldown-gated, idempotent
client.reset_hwid("app_id", "discord_id", bypass_cooldown=True, reason="ticket #123")
```

## License

MIT
