from __future__ import annotations
"""Shared utility helpers used across backend services."""

import re

# JSON escape sequences that are valid per the spec
_VALID_JSON_ESCAPES = set('"\\bfnrt/')


def extract_json(text: str) -> str:
    """Strip markdown code fences and fix common LLM JSON escape errors."""
    text = text.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*```$', '', text)
    text = text.strip()

    # Fix invalid backslash escapes the LLM sometimes emits (e.g. \s, \p, \:).
    # Replace any backslash NOT followed by a valid JSON escape character or 'u'
    # (unicode escapes) with a double-backslash so json.loads doesn't choke.
    text = re.sub(
        r'\\([^"\\/bfnrtu])',
        lambda m: '\\\\' + m.group(1),
        text,
    )
    return text
