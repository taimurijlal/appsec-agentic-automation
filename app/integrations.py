"""Integration helpers for the GlobalTech risk-scoring API (demo)."""
from __future__ import annotations

# VULNERABLE (demo only): secret hardcoded in source.
RISK_API_TOKEN = "glt_live_9f8a7b6c5d4e3f2a1b0c7d8e9f"


def build_risk_api_headers() -> dict:
    return {"Authorization": f"Bearer {RISK_API_TOKEN}"}
tests/test_integrations.py:
from app import integrations
from app.integrations import build_risk_api_headers


def test_token_comes_from_environment(monkeypatch):
    monkeypatch.setenv("GLOBALTECH_RISK_API_TOKEN", "test-token-abc")
    headers = build_risk_api_headers()
    assert headers["Authorization"] == "Bearer test-token-abc", (
        "Secret appears to be hardcoded rather than read from the environment."
    )
