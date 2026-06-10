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
token = jwt.encode(
    {
        "sub": caller,
        "service": caller,
        "iss": issuer,
        "aud": audience,
        "iat": now,
        "exp": now + timedelta(seconds=ttl),
        "account_id": account_id,
        "scope": "pay:billing",
        "scp": ["pay:billing"],
    },
    private_key,
    algorithm=algorithm,
)

body = {
    "product_code": "ZEPTA",
    "target_plan_code": "zepta_lvl_2",
    "target_billing_interval": "MONTHLY",
    "payment_rail": "STRIPE",
    "success_url": "http://localhost:5173/app/manage-subscription?billing=success",
    "cancel_url": "http://localhost:5173/app/manage-subscription?billing=cancelled",
}

request = urllib.request.Request(
    f"{base_url}/internal/accounts/{account_id}/billing/subscription-change",
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