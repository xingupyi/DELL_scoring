from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Iterable, Tuple

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..models import DistressRecord
from ..schemas import GeminiParsingError, GeminiRawResponse, ScoreRequest, ScoreResponse
from . import gemini_client


logger = logging.getLogger(__name__)


def risk_level_from_score(total_score: int) -> str:
    if total_score <= 24:
        return "Low"
    if total_score <= 44:
        return "Moderate"
    if total_score <= 64:
        return "High"
    return "Critical"


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _split_window(
    window_start: datetime, window_end: datetime
) -> Tuple[datetime, datetime, datetime]:
    midpoint = window_start + (window_end - window_start) / 2
    return window_start, midpoint, window_end


def compute_persistence_score(
    prior_records: Iterable[DistressRecord],
    *,
    window_start: datetime,
    window_end: datetime,
) -> int:
    """
    Compute persistence score P (0-33) using:
      distinct_days with EI>=15
      frequency of EI>=15
      trend_flag based on EI>=15 in early vs late half of the 7-day window
    """

    window_start = _utc(window_start)
    window_end = _utc(window_end)
    _, midpoint, _ = _split_window(window_start, window_end)

    ei_flagged = [r for r in prior_records if int(r.emotional_intensity) >= 15]
    distinct_days = len({(_utc(r.timestamp)).date() for r in ei_flagged})
    frequency = len(ei_flagged)

    trend_flag = 0
    if frequency >= 4:
        early = [int(r.emotional_intensity) for r in ei_flagged if _utc(r.timestamp) < midpoint]
        late = [int(r.emotional_intensity) for r in ei_flagged if _utc(r.timestamp) >= midpoint]
        if early and late:
            early_avg = sum(early) / len(early)
            late_avg = sum(late) / len(late)
            if late_avg >= early_avg + 5:
                trend_flag = 1

    p = 6 * distinct_days + 2 * frequency + 6 * trend_flag
    return max(0, min(33, int(p)))


def _fetch_prior_records(db: Session, user_id: str, window_start: datetime, window_end: datetime):
    stmt = (
        select(DistressRecord)
        .where(
            and_(
                DistressRecord.user_id == user_id,
                DistressRecord.timestamp >= window_start,
                DistressRecord.timestamp < window_end,
            )
        )
        .order_by(DistressRecord.timestamp.asc())
    )
    return list(db.execute(stmt).scalars().all())


async def _score_with_gemini(text: str) -> GeminiRawResponse:
    try:
        return await run_in_threadpool(gemini_client.score_text, text)
    except GeminiParsingError as exc:
        logger.warning("Gemini scoring failed after retry: %s", exc)
        raise HTTPException(status_code=502, detail="Upstream model returned invalid JSON") from exc


async def score_message(payload: ScoreRequest, db: Session) -> ScoreResponse:
    request_ts = _utc(payload.timestamp)
    window_start = request_ts - timedelta(days=7)
    window_end = request_ts  # exclude current message from history

    gemini = await _score_with_gemini(payload.text)

    prior = _fetch_prior_records(db, payload.user_id, window_start, window_end)
    persistence = compute_persistence_score(prior, window_start=window_start, window_end=window_end)

    total_score = min(100, int(gemini.emotional_intensity) + int(gemini.functional_impact) + int(persistence))
    risk_level = risk_level_from_score(total_score)

    record = DistressRecord(
        user_id=payload.user_id,
        timestamp=request_ts,
        text=payload.text,
        emotional_intensity=int(gemini.emotional_intensity),
        functional_impact=int(gemini.functional_impact),
        persistence=int(persistence),
        total_score=int(total_score),
        risk_level=risk_level,
    )
    db.add(record)
    db.commit()

    return ScoreResponse(
        emotional_intensity=int(gemini.emotional_intensity),
        functional_impact=int(gemini.functional_impact),
        persistence=int(persistence),
        total_score=int(total_score),
        risk_level=risk_level,
        ei_evidence=list(gemini.ei_evidence or [])[:3],
        fi_evidence=list(gemini.fi_evidence or [])[:3],
    )

