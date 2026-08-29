"""Integration helpers for the GlobalTech risk-scoring API (demo)."""
from __future__ import annotations

import os

TOKEN_ENV_VAR = "GLOBALTECH_RISK_API_TOKEN"


def build_risk_api_headers() -> dict:
    """Build the auth headers, reading the token from the environment.

    The credential is never stored in source; it is looked up at call time and
    the call fails closed if the environment variable is not configured.
    """
    token = os.environ.get(TOKEN_ENV_VAR)
    if not token:
        raise RuntimeError(
            f"Missing required environment variable {TOKEN_ENV_VAR!r} for the "
            "GlobalTech risk-scoring API."
        )
    return {"Authorization": f"Bearer {token}"}
