"""Deterministic mock agent: no HTTP, credentials, GitLab, or model provider."""
from transcend_v2 import triage

DIAGNOSES = {
    "pipeline_failed": ("ci_failure", "Review failed job logs and runner configuration"),
    "test_failed": ("test_regression", "Isolate failing assertion and add regression test"),
    "security_alert": ("security_review", "Ask security owner to inspect finding privately"),
    "merge_request_opened": ("review_pending", "Check coverage, ownership and required checks"),
}

def simulate(event):
    result = triage(event)
    if result["status"] != "DRAFT_REVIEW_ONLY":
        return {"status": "BLOCK", "reason": result["reason"], "agent_called": False}
    label, recommendation = DIAGNOSES[result["kind"]]
    return {"status": "MOCK_REVIEW", "diagnosis": label, "next_step": recommendation,
            "agent_called": False, "allow_merge": False, "allow_deploy": False,
            "billing_calls": 0}
