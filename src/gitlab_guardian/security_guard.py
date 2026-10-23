"""Strict security guard and credential sanitizer for CI/CD events and logs."""
from __future__ import annotations

import json
import re
from typing import Any, Dict, Tuple

# Comprehensive regex for identifying secrets and credentials
SECRET_PATTERNS = [
    re.compile(r"glpat-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
    re.compile(r"gh[pousr]_[a-zA-Z0-9]{36,}", re.IGNORECASE),
    re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{15,}", re.IGNORECASE),
    re.compile(r"(?i)(?:password|passwd|pwd|secret|api[_-]?key|access[_-]?token|private[_-]?key)\s*[:=]\s*['\"]?([^\s'\"]{6,})['\"]?"),
    re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"),
]

MAX_FIELD_LEN = 8192


def scan_for_secrets(content: str) -> Tuple[bool, str]:
    """Returns (has_secret, redaction_or_reason)."""
    for pattern in SECRET_PATTERNS:
        match = pattern.search(content)
        if match:
            return True, f"Detected sensitive pattern matching: {pattern.pattern[:30]}..."
    return False, ""


def sanitize_text(text: str) -> str:
    """Replaces any matched secrets with [REDACTED_SECRET]."""
    sanitized = text
    for pattern in SECRET_PATTERNS:
        sanitized = pattern.sub("[REDACTED_SECRET]", sanitized)
    return sanitized


def validate_event_schema(event: Dict[str, Any]) -> Tuple[bool, str]:
    """Fail-closed schema validation for incoming webhook / pipeline events."""
    if not isinstance(event, dict):
        return False, "event_must_be_dict"

    required = {"kind", "project", "summary"}
    if not required.issubset(event.keys()):
        return False, f"missing_required_fields: {required - event.keys()}"

    allowed_kinds = {"pipeline_failed", "test_failed", "security_alert", "merge_request_opened"}
    if event["kind"] not in allowed_kinds:
        return False, f"unsupported_event_kind: {event['kind']}"

    for k, val in event.items():
        if isinstance(val, str) and len(val) > MAX_FIELD_LEN:
            return False, f"field_exceeds_max_len: {k}"

    # Check for secrets inside payload
    serialized = json.dumps(event, ensure_ascii=False)
    has_secret, reason = scan_for_secrets(serialized)
    if has_secret:
        return False, f"sensitive_data_in_event: {reason}"

    return True, "valid"
