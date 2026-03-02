from datetime import datetime, timedelta, timezone

from app.models import DistressRecord
from app.services.scoring import compute_persistence_score


def _ts(days_ago: float) -> datetime:
    base = datetime(2025, 1, 8, 12, 0, 0, tzinfo=timezone.utc)
    return base - timedelta(days=days_ago)


def test_persistence_trend_flag_and_cap():
    window_end = _ts(0)
    window_start = window_end - timedelta(days=7)

    # Construct prior records over the 7-day window with EI>=15.
    # Early window: moderate EI.
    early_records = [
        DistressRecord(
            user_id="u1",
            timestamp=_ts(6),
            text="",
            emotional_intensity=16,
            functional_impact=0,
            persistence=0,
            total_score=0,
            risk_level="Low",
        ),
        DistressRecord(
            user_id="u1",
            timestamp=_ts(5.5),
            text="",
            emotional_intensity=18,
            functional_impact=0,
            persistence=0,
            total_score=0,
            risk_level="Low",
        ),
    ]

    # Late window: significantly higher EI to trigger trend_flag.
    late_records = [
        DistressRecord(
            user_id="u1",
            timestamp=_ts(1),
            text="",
            emotional_intensity=30,
            functional_impact=0,
            persistence=0,
            total_score=0,
            risk_level="Low",
        ),
        DistressRecord(
            user_id="u1",
            timestamp=_ts(0.5),
            text="",
            emotional_intensity=31,
            functional_impact=0,
            persistence=0,
            total_score=0,
            risk_level="Low",
        ),
    ]

    prior = early_records + late_records

    p = compute_persistence_score(prior, window_start=window_start, window_end=window_end)

    # distinct_days: 4, frequency: 4, trend_flag: 1
    # P = 6*4 + 2*4 + 6*1 = 24 + 8 + 6 = 38 -> capped at 33
    assert p == 33

