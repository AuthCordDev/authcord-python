"""Real-time session kick via the heartbeat loop.

When an admin clicks Terminate in the AuthCord dashboard, the user's
client app should disconnect within ~10 seconds. This is done by
running a background heartbeat after the initial validate call.
"""

import sys
import time

from authcord import AuthCordClient, HeartbeatResult


client = AuthCordClient(api_key="ac_your_api_key_here")

APP_ID = "your_app_id"
DISCORD_ID = "123456789012345678"
HWID = "PC-12345"

# Step 1: standard validate at startup.
result = client.validate(app_id=APP_ID, discord_id=DISCORD_ID, hwid=HWID)
if not result.valid:
    print(f"Access denied: {result.reason}")
    sys.exit(1)

print(f"Access granted for {result.user.username}")


# Step 2: hook into termination. The callback fires exactly once when
# the server returns valid=False (admin clicked Terminate, user banned,
# product expired, etc.) and then the loop stops on its own.
def on_terminated(hb: HeartbeatResult) -> None:
    print(f"\nSession ended by AuthCord: {hb.reason}")
    # Tear down whatever your app is doing — close windows, clear
    # secrets in memory, redirect to login, etc. Calling sys.exit here
    # is the simplest pattern for a CLI / single-window desktop app.
    sys.exit(0)


def on_error(err: Exception) -> None:
    # Network errors are non-fatal — the loop keeps polling. Log them
    # for visibility but don't crash the user out of the app.
    print(f"[heartbeat] transient error: {err}", file=sys.stderr)


# start_heartbeat runs in a daemon thread, so it doesn't block your
# app. Default interval is server-controlled (~10s).
loop = client.start_heartbeat(
    app_id=APP_ID,
    discord_id=DISCORD_ID,
    hwid=HWID,
    on_terminated=on_terminated,
    on_error=on_error,
)

try:
    # ... your actual app does its thing here ...
    print("App running. The heartbeat will kick us off if an admin terminates the session.")
    while True:
        time.sleep(1)
finally:
    # On normal exit (user signs out, app closes), stop the loop
    # cleanly so the thread doesn't outlive the process.
    loop.stop()
    client.close()
