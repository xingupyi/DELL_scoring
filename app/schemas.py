from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator


class ScoreRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    timestamp: datetime
    text: str = Field(..., min_length=1)

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class GeminiRawResponse(BaseModel):
    emotional_intensity: int = Field(ge: 0, le: 33)
    functional_impact: int = Field(ge: 0, le: 33)
    ei_evidence: Optional[List[str]] = Field(default=None, max_length=3)
    fi_evidence: Optional[List[str]] = Field(default=None, max_length=3)

    @field_validator("ei_evidence", "fi_evidence", mode="before")
    @classmethod
    def default_empty_list(cls, value):
        if value is None:
            return []
        return value

    @field_validator("emotional_intensity", "functional_impact", mode="before")
    @classmethod
    def clamp_scores(cls, value: int) -> int:
        # Allow slight out-of-range values and clamp; Pydantic bounds will enforce final range.
        if value is None:
            raise ValueError("Score is required")
        return max(0, min(33, int(value)))


class ScoreResponse(BaseModel):
    emotional_intensity: int
    functional_impact: int
    persistence: int
    total_score: int
    risk_level: str
    ei_evidence: List[str] = Field(default_factory=list)
    fi_evidence: List[str] = Field(default_factory=list)


class GeminiParsingError(Exception):
    """Raised when Gemini output cannot be parsed or validated."""

    def __init__(self, message: str, raw_output: str | None = None, validation_error: ValidationError | None = None):
        super().__init__(message)
        self.raw_output = raw_output
        self.validation_error = validation_error

