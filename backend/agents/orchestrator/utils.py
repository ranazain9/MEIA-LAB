"""
Orchestrator Utilities
======================

Helpers for prompt formatting, token counting,
and output sanitization.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict

logger = logging.getLogger(__name__)


def truncate_to_token_limit(
    text: str,
    max_chars: int = 12_000,
) -> str:
    """
    Rough truncation to stay within LLM context limits.
    Uses character count as a proxy (≈ 4 chars per token).
    """
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n[... truncated ...]"


def sanitize_json_output(raw: str) -> Dict[str, Any]:
    """
    Extract and parse JSON from LLM output that may contain
    markdown fences or extra text.
    """
    # Try to find JSON block
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        return json.loads(match.group(1))

    # Try direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Could not parse LLM output as JSON.")
        return {"raw_output": raw}


def format_prompt(template: str, **kwargs: Any) -> str:
    """Safely format a prompt template with kwargs."""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logger.error("Missing prompt variable: %s", e)
        raise
