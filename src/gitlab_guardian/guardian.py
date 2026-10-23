"""Offline fail-closed GitLab Agent Platform readiness checker. No network/writes."""
import argparse
import json
import pathlib


def assess(data):
    required = (
        "seat_assigned", "community_role", "agent_platform_enabled",
        "credit_balance_verified", "zero_cost_guaranteed", "runner_explicitly_enabled",
    )
    if not isinstance(data, dict) or any(k not in data for k in required):
        return {"decision": "BLOCK", "reason": "missing_evidence", "may_execute": False}
    if data["community_role"] not in ("Developer", "Maintainer", "Owner") or data["seat_assigned"] is not True:
        return {"decision": "BLOCK", "reason": "no_valid_access", "may_execute": False}
    if data["agent_platform_enabled"] is not True:
        return {"decision": "BLOCK", "reason": "agent_platform_unverified", "may_execute": False}
    if data["credit_balance_verified"] is not True or data["zero_cost_guaranteed"] is not True:
        return {"decision": "BLOCK", "reason": "cost_unverified", "may_execute": False}
    if data["runner_explicitly_enabled"] is not True:
        return {"decision": "BLOCK", "reason": "execution_router_disabled", "may_execute": False}
    return {"decision": "ELIGIBLE_FOR_SEPARATE_APPROVAL", "reason": "all_attestations_present", "may_execute": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence", type=pathlib.Path)
    args = parser.parse_args()
    print(json.dumps(assess(json.loads(args.evidence.read_text())), sort_keys=True))


if __name__ == "__main__":
    main()
