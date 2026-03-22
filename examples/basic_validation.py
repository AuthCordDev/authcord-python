"""Basic validation example."""

from authcord import AuthCordClient

client = AuthCordClient(api_key="ac_your_api_key_here")

result = client.validate(
    discord_id="123456789012345678",
    app_id="your_app_id",
    hwid="PC-12345",
)

if result.valid:
    print(f"Access granted for {result.user.username}")
    print(f"Mode: {result.mode}")
    print(f"Entitlements: {result.entitlements}")
    for product in result.products:
        status = "Lifetime" if product.is_lifetime else f"Expires {product.expires_at}"
        print(f"  - {product.name}: {status}")
else:
    print(f"Access denied: {result.reason}")
    if result.banned:
        print("User is banned")

client.close()
