"""
claude_zt/validator.py — Input Validation (Foundation Tier)

Sanitizes every query before it reaches the retrieval pipeline or LLM.

Why this matters:
The Anthropic Zero Trust ebook confirms LLMs cannot reliably distinguish
informational context from actionable instructions. Algorithmic prompt
injection attacks achieve 100% success rates across model families.

Foundation tier defense: remove known injection patterns,
enforce length limits, strip control characters.
This is not a complete solution — it's the baseline that removes
the easiest attacks. Architecture (privilege scoping) is the real defense.
"""

import re
from dataclasses import dataclass


# Patterns associated with prompt injection attempts
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"disregard\s+(all\s+)?(previous|prior|above)\s+instructions?",
    r"forget\s+(everything|all|your instructions)",
    r"you are now",
    r"new\s+persona",
    r"act\s+as\s+(a\s+)?(?!field ciso|security analyst|researcher)",
    r"jailbreak",
    r"dan\s+mode",
    r"developer\s+mode",
    r"<\s*script",
    r"system\s*:\s*you",
]

MAX_QUERY_LENGTH = 2000
MIN_QUERY_LENGTH = 3


@dataclass
class ValidationResult:
    is_valid: bool
    cleaned_query: str
    warnings: list


def validate_query(query: str) -> ValidationResult:
    """
    Validate and sanitize a user query.
    Returns a ValidationResult with cleaned text and any warnings.
    """
    warnings = []

    # Strip leading/trailing whitespace
    cleaned = query.strip()

    # Length checks
    if len(cleaned) < MIN_QUERY_LENGTH:
        return ValidationResult(
            is_valid=False,
            cleaned_query=cleaned,
            warnings=["Query too short — minimum 3 characters"]
        )

    if len(cleaned) > MAX_QUERY_LENGTH:
        cleaned = cleaned[:MAX_QUERY_LENGTH]
        warnings.append(f"Query truncated to {MAX_QUERY_LENGTH} characters")

    # Strip control characters (keep newlines for multi-line queries)
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', cleaned)

    # Check for injection patterns
    lower = cleaned.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower):
            return ValidationResult(
                is_valid=False,
                cleaned_query=cleaned,
                warnings=[f"Query contains pattern associated with prompt injection: '{pattern}'"]
            )

    return ValidationResult(
        is_valid=True,
        cleaned_query=cleaned,
        warnings=warnings
    )
