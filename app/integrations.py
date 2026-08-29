"""Integration helpers for the GlobalTech risk-scoring API (demo)."""
from __future__ import annotations

import os

#: Name of the environment variable holding the risk API bearer token.
RISK_API_TOKEN_ENV = "GLOBALTECH_RISK_API_TOKEN"


def build_risk_api_headers() -> dict:
    token = os.environ.get(RISK_API_TOKEN_ENV)
    if not token:
        raise RuntimeError(
            f"Missing required environment variable {RISK_API_TOKEN_ENV}: "
            "the risk API token must be supplied via configuration or a secrets manager."
        )
    return {"Authorization": f"Bearer {token}"}
