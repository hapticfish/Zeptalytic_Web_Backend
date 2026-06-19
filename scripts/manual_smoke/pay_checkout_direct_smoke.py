from datetime import UTC, datetime, timedelta
import json
import os
import urllib.error
import urllib.request

import jwt

account_id = "ead88ae0-c96c-408c-82c8-d29ca595b6b0"
base_url = os.environ["PAY_SERVICE_BASE_URL"].rstrip("/")

private_key = os.environ["PAY_SERVICE_INTERNAL_JWT_PRIVATE_KEY"].replace("\\n", "\n")
issuer = os.environ["PAY_SERVICE_INTERNAL_JWT_ISSUER"]
audience = os.environ["PAY_SERVICE_INTERNAL_JWT_AUDIENCE"]
caller = os.environ["PAY_SERVICE_INTERNAL_JWT_CALLER"]
algorithm = os.environ.get("PAY_SERVICE_INTERNAL_JWT_ALGORITHM", "RS256")
ttl = int(os.environ.get("PAY_SERVICE_INTERNAL_JWT_TTL_SECONDS", "300"))

now = datetime.now(UTC)
claims = {
    "sub": caller,
    "service": caller,
    "iss": issuer,
    "aud": audience,
    "iat": now,
    "exp": now + timedelta(seconds=ttl),
    "account_id": account_id,
    "scope": "pay:billing",
    "scp": ["pay:billing"],
}

token = jwt.encode(claims, private_key, algorithm=algorithm)

print("JWT header:", jwt.get_unverified_header(token))
print("JWT claims:", jwt.decode(token, options={"verify_signature": False}))

body = {
    "purchase_type": "product",
    "product_code": "ZEPTA",
    "plan_code": "zepta_lvl_3",
    "billing_interval": "MONTHLY",
    "payment_rail": "STRIPE",
    "success_url": "http://localhost:5173/app/manage-subscription?billing=success",
    "cancel_url": "http://localhost:5173/app/manage-subscription?billing=cancelled",
}

request = urllib.request.Request(
    f"{base_url}/internal/accounts/{account_id}/billing/checkout",
    data=json.dumps(body).encode("utf-8"),
    headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    },
    method="POST",
)

try:
    with urllib.request.urlopen(request, timeout=20) as response:
        print("status:", response.status)
        print(response.read().decode("utf-8", errors="replace"))
except urllib.error.HTTPError as exc:
    print("status:", exc.code)
    print(exc.read().decode("utf-8", errors="replace"))
except Exception as exc:
    print("error:", repr(exc))