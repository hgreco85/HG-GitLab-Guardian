"""GitLab Duo Agent Platform connector: implements custom agent specs, tools, and execution flows."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from pipeline_triage import TriageDiagnosis, analyze_pipeline_log
from remediation import MergeRequestProposal, generate_remediation
from security_guard import validate_event_schema


# Custom GitLab Duo Agent definition schema
GITLAB_DUO_AGENT_SPEC = {
    "name": "gitlab-guardian",
    "display_name": "GitLab Guardian: Post-Code Incident Commander",
    "version": "2.0.0",
    "description": "Autonomous post-code agent for GitLab Duo: triages failing pipelines, isolates test regressions, crafts reproduction tests, and submits remediating merge requests with strict human approval gates.",
    "capabilities": [
        "gitlab:pipelines:read",
        "gitlab:issues:read_write",
        "gitlab:merge_requests:create",
        "gitlab:duo_chat:respond",
    ],
    "tools": [
        {
            "name": "triage_pipeline_failure",
            "description": "Analyzes raw GitLab CI job logs, identifies failure category (test regression, security CVE, secret leak), and calculates confidence score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "job_log": {"type": "string", "description": "Raw terminal output of the failed job"},
                    "event_summary": {"type": "string", "description": "Short summary of pipeline failure event"},
                },
                "required": ["job_log"],
            },
        },
        {
            "name": "generate_remediation_proposal",
            "description": "Generates a minimal diff patch, reproducible test suite, and structured Merge Request draft.",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "string", "description": "Canonical identifier for the incident"},
                    "diagnosis": {"type": "object", "description": "Triage diagnosis dictionary"},
                },
                "required": ["incident_id", "diagnosis"],
            },
        },
        {
            "name": "request_human_approval",
            "description": "Posts an approval boundary notification on GitLab Issue or Merge Request requiring maintainer sign-off before any merge or production deploy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mr_id": {"type": "string"},
                    "checklist": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["mr_id"],
            },
        },
    ],
}


class GitLabDuoAgent:
    """Agent running within the GitLab Duo Agent Platform."""

    def __init__(self, agent_name: str = "gitlab-guardian"):
        self.agent_name = agent_name
        self.spec = GITLAB_DUO_AGENT_SPEC
        self.call_history: List[Dict[str, Any]] = []

    def handle_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches an incoming GitLab webhook event through the Duo Agent lifecycle."""
        is_valid, reason = validate_event_schema(event)
        if not is_valid:
            return {
                "status": "REJECTED_FAIL_CLOSED",
                "reason": reason,
                "agent_invoked": False,
                "mr_created": False,
            }

        job_log = event.get("job_log", event.get("summary", ""))
        diagnosis = self.triage_pipeline_failure(job_log, event.get("summary", ""))
        proposal = self.generate_remediation_proposal(event.get("project", "incident-001"), diagnosis)

        record = {
            "event_kind": event["kind"],
            "diagnosis": diagnosis.to_dict(),
            "proposal": proposal.to_dict(),
            "cost_usd": 0.0,
            "duo_native": True,
        }
        self.call_history.append(record)

        return {
            "status": "REMEDIATION_PROPOSED_AWAITING_APPROVAL",
            "agent_invoked": True,
            "diagnosis": diagnosis.to_dict(),
            "proposal": proposal.to_dict(),
            "approval_gate": {
                "required": True,
                "status": "PENDING_MAINTAINER_REVIEW",
            },
            "cost_usd": 0.0,
        }

    def triage_pipeline_failure(self, job_log: str, summary: str = "") -> TriageDiagnosis:
        return analyze_pipeline_log(job_log, summary)

    def generate_remediation_proposal(self, incident_id: str, diagnosis: TriageDiagnosis) -> MergeRequestProposal:
        return generate_remediation(diagnosis, incident_id)
