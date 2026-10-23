"""Read-only, offline demonstration for three synthetic post-code incidents."""
import json
from mock_agent import simulate

SCENARIOS = (
    ("ci_failure", {"kind": "pipeline_failed", "project": "fictional/demo",
                    "summary": "unit-test job failed after dependency update"}),
    ("security_advisory", {"kind": "security_alert", "project": "fictional/demo",
                           "summary": "dependency advisory requires review"}),
    ("secret_contamination", {"kind": "test_failed", "project": "fictional/demo",
                              "summary": "Authorization: Bearer SYNTHETIC_EXAMPLE_NOT_A_SECRET"}),
)

def demonstrate():
    cases = []
    for name, event in SCENARIOS:
        result = simulate(event)
        cases.append({"scenario": name, "decision": result["status"],
                      "diagnosis": result.get("diagnosis"), "reason": result.get("reason"),
                      "agent_called": result["agent_called"],
                      "allow_merge": result.get("allow_merge", False),
                      "allow_deploy": result.get("allow_deploy", False)})
    return {"mode": "OFFLINE_MOCK", "cases": cases, "cost_usd": 0,
            "external_calls": 0, "real_gitlab_agent_used": False}

if __name__ == "__main__":
    print(json.dumps(demonstrate(), indent=2, sort_keys=True))
