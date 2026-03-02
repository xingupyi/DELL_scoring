from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

import vertexai
from vertexai.generative_models import GenerationConfig, GenerativeModel

from ..config import settings
from ..schemas import GeminiParsingError, GeminiRawResponse


logger = logging.getLogger(__name__)


GEMINI_RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "emotional_intensity": {"type": "integer", "minimum": 0, "maximum": 33},
        "functional_impact": {"type": "integer", "minimum": 0, "maximum": 33},
        "ei_evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
        "fi_evidence": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
    },
    "required": ["emotional_intensity", "functional_impact"],
}


PROMPT_TEMPLATE = """You are scoring a short text for distress signals.

Return ONLY valid JSON matching the provided schema.

Scoring rubric (0-33 each):
- emotional_intensity: strength of expressed emotional distress
- functional_impact: impact on daily functioning / motivation / self-care / work/school

Evidence:
- ei_evidence: up to 3 short substrings/phrases from the text supporting emotional_intensity
- fi_evidence: up to 3 short substrings/phrases from the text supporting functional_impact

Text:
{text}
"""


def _extract_json_object(s: str) -> str:
    """Best-effort extraction of the first JSON object from a string."""

    start = s.find("{")
    end = s.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise GeminiParsingError("No JSON object found in Gemini output", raw_output=s)
    return s[start : end + 1]


@dataclass(frozen=True)
class GeminiClient:
    model: GenerativeModel
    generation_config: GenerationConfig

    def score_text_once(self, text: str) -> GeminiRawResponse:
        prompt = PROMPT_TEMPLATE.format(text=text)
        response = self.model.generate_content(prompt, generation_config=self.generation_config)

        raw_text: Optional[str] = getattr(response, "text", None)
        if not raw_text:
            raw_text = str(response)

        try:
            json_str = _extract_json_object(raw_text)
            data = json.loads(json_str)
            return GeminiRawResponse.model_validate(data)
        except GeminiParsingError:
            raise
        except Exception as exc:
            raise GeminiParsingError("Failed to parse/validate Gemini JSON output", raw_output=raw_text) from exc


def build_gemini_client() -> GeminiClient:
    vertexai.init(project=settings.vertex_project_id, location=settings.vertex_location)

    model = GenerativeModel(settings.vertex_model_name)
    config = GenerationConfig(
        temperature=settings.vertex_temperature,
        response_mime_type="application/json",
        response_schema=GEMINI_RESPONSE_SCHEMA,
    )
    return GeminiClient(model=model, generation_config=config)


_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    global _client
    if _client is None:
        _client = build_gemini_client()
    return _client


def score_text(text: str, *, retry_once: bool = True) -> GeminiRawResponse:
    """
    Score text via Gemini with a single retry on JSON/validation failures.

    Raises GeminiParsingError if parsing fails even after retry.
    """

    client = get_gemini_client()
    try:
        return client.score_text_once(text)
    except GeminiParsingError as first_err:
        logger.warning("Gemini parsing failed (first attempt): %s", first_err)
        if not retry_once:
            raise
        return client.score_text_once(text)

