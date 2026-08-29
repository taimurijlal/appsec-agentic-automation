from app import integrations
from app.integrations import build_risk_api_headers


def test_token_comes_from_environment(monkeypatch):
    monkeypatch.setenv("GLOBALTECH_RISK_API_TOKEN", "test-token-abc")
    headers = build_risk_api_headers()
    assert headers["Authorization"] == "Bearer test-token-abc", (
        "Secret appears to be hardcoded rather than read from the environment."
    )
