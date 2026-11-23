"""Conservative output safety check for tutor and writing-coach replies.

This is a small heuristic layer, not a substitute for a dedicated moderation
service. It is intentionally narrow to avoid punishing legitimate French
learning content; anything flagged is replaced with a safe, honest message.
"""

from __future__ import annotations

import re

SAFE_REPLY = (
    "I can't help with that. I'm here to help you learn French — "
    "ask me about vocabulary, grammar, pronunciation or a practice task instead."
)

# Prompt-injection / instruction-leakage phrases in model output.
_INJECTION_PATTERNS = (
    r"ignore (all |any )?(previous|prior|above|earlier) instructions",
    r"here (is|are) (the |my )?(system prompt|internal instructions)",
    r"developer mode (enabled|activated)",
    r"you are now (a|an) (unrestricted|different) (ai|assistant)",
)

# Clearly harmful content. Kept short and unambiguous; do not add ordinary
# French grammar terms or sensitive-topic vocabulary that learners need.
_HARM_PATTERNS = (
    r"\b(how to (make|build) (a )?(bomb|weapon))\b",
    r"\b(hate|kill) (all )?(jews|muslims|immigrants|nepali|french people)\b",
)

_COMPILED = tuple(re.compile(p, re.IGNORECASE) for p in _INJECTION_PATTERNS + _HARM_PATTERNS)


def check_output(text: str) -> tuple[bool, str]:
    """Return (allowed, reason). Missing/empty text is allowed (callers handle it)."""
    if not text:
        return True, ""
    for pattern in _COMPILED:
        match = pattern.search(text)
        if match:
            return False, match.group(0)[:80]
    return True, ""


def sanitize_output(text: str) -> tuple[str, bool]:
    """Return (text_to_show, was_blocked)."""
    allowed, _ = check_output(text)
    return (text, False) if allowed else (SAFE_REPLY, True)
