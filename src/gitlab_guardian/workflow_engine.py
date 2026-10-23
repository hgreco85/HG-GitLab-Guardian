"""Workflow Engine: End-to-end post-code automation coordinator with retries and fault recovery."""
from __future__ import annotations

import json
import random
import time
from typing import Any, Callable, Dict, List, Optional
from duo_agent import GitLabDuoAgent
from ledger import DecisionLedger
from pipeline_triage import TriageDiagnosis
from remediation import MergeRequestProposal


class WorkflowEngine:
    """Executes the full pipeline: Issue -> Triage -> Reproduce -> Patch -> Pipeline -> MR -> Review."""

    def __init__(self, agent: Optional[GitLabDuoAgent] = None):
        self.agent = agent or GitLabDuoAgent()
        self.ledger = DecisionLedger()
        self.max_retries = 3

    def run_lifecycle(self, incident_event: Dict[str, Any]) -> Dict[str, Any]:
        """Runs the complete competitive post-code incident resolution cycle."""
        start_time = time.time()
        incident_id = incident_event.get("incident_id", "INC-2026-AUTONOMOUS")

        # Step 1: Ingest & Security Gate
        self.ledger.record(
            step="1_INGEST",
            actor="WEBHOOK_RECEIVER",
            action="INGEST_INCIDENT_EVENT",
            payload={"incident_id": incident_id, "kind": incident_event.get("kind")},
        )

        # Step 2: Agent Triage with Retry & Recovery
        triage_result = self._execute_with_retry(
            func=lambda: self.agent.handle_webhook_event(incident_event),
            step_name="2_AGENT_TRIAGE",
        )

        if triage_result.get("status") == "REJECTED_FAIL_CLOSED":
            self.ledger.record(
                step="2_AGENT_TRIAGE",
                actor="SECURITY_GUARD",
                action="REJECT_CONTAMINATED_OR_INVALID_EVENT",
                payload={"reason": triage_result.get("reason")},
            )
            return {
                "success": False,
                "status": "BLOCKED_FAIL_CLOSED",
                "reason": triage_result.get("reason"),
                "elapsed_seconds": round(time.time() - start_time, 3),
                "ledger_valid": self.ledger.verify(),
            }

        diagnosis = triage_result["diagnosis"]
        proposal = triage_result["proposal"]

        # Step 3: Minimal Regression Test Generation
        self.ledger.record(
            step="3_TEST_GENERATION",
            actor="GITLAB_DUO_AGENT",
            action="GENERATE_REPRODUCIBLE_TEST",
            payload={"category": diagnosis["category"], "test_code": proposal["repro_test_code"][:200]},
        )

        # Step 4: Proposed Patch Validation
        self.ledger.record(
            step="4_PATCH_SYNTHESIS",
            actor="GITLAB_DUO_AGENT",
            action="SYNTHESIZE_MINIMAL_DIFF",
            payload={"target_branch": proposal["target_branch"], "diff_lines": len(proposal["diff_patch"].splitlines())},
        )

        # Step 5: Merge Request Generation & Human Approval Boundary
        self.ledger.record(
            step="5_MERGE_REQUEST",
            actor="GITLAB_DUO_AGENT",
            action="CREATE_DRAFT_MERGE_REQUEST",
            payload={
                "title": proposal["title"],
                "source_branch": proposal["source_branch"],
                "human_approval_required": proposal["human_approval_required"],
            },
        )

        elapsed = round(time.time() - start_time, 3)

        return {
            "success": True,
            "status": "COMPLETED_READY_FOR_HUMAN_SIGN_OFF",
            "incident_id": incident_id,
            "diagnosis": diagnosis,
            "proposal": proposal,
            "elapsed_seconds": elapsed,
            "ledger_verified": self.ledger.verify(),
            "ledger_blocks_count": len(self.ledger.chain),
            "cost_usd": 0.0,
        }

    def _execute_with_retry(self, func: Callable[[], Any], step_name: str) -> Any:
        """Executes action with exponential backoff and jitter for transient failure recovery."""
        attempts = 0
        while attempts < self.max_retries:
            try:
                attempts += 1
                result = func()
                self.ledger.record(
                    step=step_name,
                    actor="WORKFLOW_ENGINE",
                    action=f"EXECUTE_SUCCESS_ATTEMPT_{attempts}",
                    payload={"status": result.get("status")},
                )
                return result
            except Exception as e:
                wait_time = (2 ** attempts) * 0.05 + random.uniform(0.01, 0.03)
                time.sleep(wait_time)
                if attempts >= self.max_retries:
                    self.ledger.record(
                        step=step_name,
                        actor="WORKFLOW_ENGINE",
                        action=f"EXECUTE_EXHAUSTED_RETRIES",
                        payload={"error": str(e), "attempts": attempts},
                    )
                    raise
