"""Offline deterministic synthetic benchmark. No random services or paid execution."""
import json
from mock_agent import simulate

CASES = [
    ({"kind": "pipeline_failed", "summary": "runner exited with code 1"}, "ci_failure"),
    ({"kind": "test_failed", "summary": "assertion mismatch"}, "test_regression"),
    ({"kind": "security_alert", "summary": "dependency advisory"}, "security_review"),
    ({"kind": "merge_request_opened", "summary": "ready for review"}, "review_pending"),
    ({"kind": "something_else", "summary": "unexpected"}, None),
    ({"kind": [], "summary": "malformed"}, None),
    ({"kind": "test_failed", "summary": "password=123"}, None),
    ({"kind": "pipeline_failed", "summary": "should reject extra field", "command": "rm -rf /"}, None),
]

def evaluate():
    results = []
    for event, expected in CASES:
        output = simulate(event)
        correct = (output.get("diagnosis") == expected and
                   output["agent_called"] is False and
                   output.get("allow_deploy", False) is False and
                   output.get("allow_merge", False) is False)
        results.append({"kind": str(event["kind"]), "pass": correct})
    return {"scenarios": len(results), "passed": sum(x["pass"] for x in results),
            "failed": sum(not x["pass"] for x in results), "results": results}

if __name__ == "__main__":
    print(json.dumps(evaluate(), sort_keys=True))
