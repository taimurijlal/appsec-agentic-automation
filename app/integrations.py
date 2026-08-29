"""Integration helpers for the GlobalTech risk-scoring API (demo)."""
from __future__ import annotations

import os

RISK_API_TOKEN_ENV_VAR = "GLOBALTECH_RISK_API_TOKEN"


def build_risk_api_headers() -> dict:
    token = os.environ.get(RISK_API_TOKEN_ENV_VAR)
    if not token:
        raise RuntimeError(
            f"Missing required environment variable {RISK_API_TOKEN_ENV_VAR!r} "
            "for the GlobalTech risk-scoring API."
        )
    return {"Authorization": f"Bearer {token}"}
