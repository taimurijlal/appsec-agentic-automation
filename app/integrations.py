"""Integration helpers for the GlobalTech risk-scoring API (demo)."""
from __future__ import annotations

import os

# The API token is never stored in source control; it is read at runtime from
# the RISK_API_TOKEN environment variable (or a secrets manager that populates
# it). Missing configuration fails closed.
RISK_API_TOKEN = os.environ.get("RISK_API_TOKEN")


def build_risk_api_headers() -> dict:
    token = os.environ.get("RISK_API_TOKEN", RISK_API_TOKEN)
    if not token:
        raise RuntimeError(
            "RISK_API_TOKEN is not configured; set it in the environment "
            "before calling the risk-scoring API."
        )
    return {"Authorization": f"Bearer {token}"}
