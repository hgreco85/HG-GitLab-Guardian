"""Offline policy-only incident triage. Never runs external processes or agents."""
import json
import re
import sys

ALLOWED = frozenset({"pipeline_failed", "test_failed", "security_alert", "merge_request_opened"})
FIELDS = frozenset({"kind", "project", "url", "summary"})
SENSITIVE = re.compile(r"(?i)(password|passwd|secret|api[_-]?key|access[_-]?token|token[ \\t]*[:=]|bearer\s+|authorization|private[_-]?key|credential|gh[pousr]_[a-z0-9]+|glpat-|sk-[a-z0-9]+)")

def triage(event):
    if not isinstance(event, dict) or set(event) - FIELDS:
        return {"status": "BLOCK", "reason": "invalid_event"}
    if not isinstance(event.get("kind"), str) or event["kind"] not in ALLOWED:
        return {"status": "BLOCK", "reason": "invalid_event"}
    for k in ("project", "url", "summary"):
        if k in event and (not isinstance(event[k], str) or len(event[k]) > 2048):
            return {"status": "BLOCK", "reason": "invalid_event"}
    if not isinstance(event.get("summary"), str) or not event["summary"].strip():
        return {"status": "BLOCK", "reason": "invalid_event"}
    if any(ord(ch) < 32 and ch not in "\t\n\r" for val in event.values() for ch in val):
        return {"status": "BLOCK", "reason": "invalid_event"}
    if SENSITIVE.search(json.dumps(event, ensure_ascii=False)):
        return {"status": "BLOCK", "reason": "sensitive_data"}
    return {"status": "DRAFT_REVIEW_ONLY", "kind": event["kind"],
            "recommendation": "human_review_required", "allow_agent": False,
            "allow_merge": False, "allow_deploy": False}

if __name__ == "__main__":
    try:
        print(json.dumps(triage(json.load(sys.stdin)), sort_keys=True))
    except (ValueError, TypeError):
        print(json.dumps({"status": "BLOCK", "reason": "invalid_json"}))
