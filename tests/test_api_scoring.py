from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.schemas import GeminiRawResponse
from app.services import gemini_client


def _make_payload(timestamp: datetime):
    return {
        "user_id": "user-1",
        "timestamp": timestamp.isoformat(),
        "text": "example text",
    }


def test_risk_bands_without_persistence(client: TestClient, fixed_timestamp, monkeypatch):
    """Ensure risk bands map correctly when persistence is zero (no history)."""

    cases = [
        (5, 5, "Low"),
        (15, 12, "Moderate"),
        (20, 25, "High"),
        (30, 30, "Critical"),
    ]

    def fake_score_factory(ei: int, fi: int):
        def fake_score(_text: str) -> GeminiRawResponse:
            return GeminiRawResponse(
                emotional_intensity=ei,
                functional_impact=fi,
                ei_evidence=["ei"],
                fi_evidence=["fi"],
            )

        return fake_score

    for ei, fi, expected_band in cases:
        monkeypatch.setattr(gemini_client, "score_text", fake_score_factory(ei, fi))
        resp = client.post("/score", json=_make_payload(fixed_timestamp))
        assert resp.status_code == 200
        data = resp.json()
        assert data["risk_level"] == expected_band
        # With no history, persistence should be zero.
        assert data["persistence"] == 0

