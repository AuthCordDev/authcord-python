"""Offline token example for desktop applications."""

from pathlib import Path
from authcord import AuthCordClient, OfflineTokenError

CACHE_DIR = Path.home() / ".myapp"
CACHE_DIR.mkdir(exist_ok=True)

APP_ID = "your_app_id"
API_KEY = "ac_your_api_key_here"
DISCORD_ID = "123456789012345678"
HWID = "PC-12345"


def online_flow():
    """When online: validate and cache offline token."""
    client = AuthCordClient(api_key=API_KEY)

    # Cache public key
    pub_key = client.get_public_key(app_id=APP_ID)
    (CACHE_DIR / "public_key.txt").write_text(pub_key.public_key)

    # Get offline token
    token = client.get_offline_token(discord_id=DISCORD_ID, app_id=APP_ID, hwid=HWID, ttl=24)
    (CACHE_DIR / "offline_token.txt").write_text(token.token)

    client.close()
    print("Online validation successful, tokens cached")


def offline_flow():
    """When offline: verify cached token locally."""
    token = (CACHE_DIR / "offline_token.txt").read_text()
    public_key = (CACHE_DIR / "public_key.txt").read_text()

    client = AuthCordClient(api_key="unused")
    result = client.verify_offline(token=token, public_key=public_key, hwid=HWID)
    client.close()

    if result.valid:
        print(f"Offline access granted for {result.user.username}")
    else:
        print(f"Offline access denied: {result.reason}")


try:
    online_flow()
except Exception as e:
    print(f"Online failed: {e}, trying offline...")
    try:
        offline_flow()
    except OfflineTokenError as e:
        print(f"Offline failed: {e}")
