"""Unit tests for GitLab Duo Agent Platform integration."""
import unittest
from duo_agent import GitLabDuoAgent, GITLAB_DUO_AGENT_SPEC


class TestGitLabDuoAgent(unittest.TestCase):
    def setUp(self):
        self.agent = GitLabDuoAgent()

    def test_spec_compliance(self):
        self.assertEqual(self.agent.spec["name"], "gitlab-guardian")
        self.assertIn("gitlab:pipelines:read", self.agent.spec["capabilities"])
        self.assertIn("gitlab:merge_requests:create", self.agent.spec["capabilities"])
        tool_names = [t["name"] for t in self.agent.spec["tools"]]
        self.assertIn("triage_pipeline_failure", tool_names)
        self.assertIn("generate_remediation_proposal", tool_names)

    def test_handle_valid_pipeline_failed_event(self):
        event = {
            "kind": "pipeline_failed",
            "project": "hg-stack-group/demo",
            "summary": "unit-test job failed after dependency bump",
            "job_log": "AssertionError: expected True got False",
        }
        res = self.agent.handle_webhook_event(event)
        self.assertEqual(res["status"], "REMEDIATION_PROPOSED_AWAITING_APPROVAL")
        self.assertTrue(res["agent_invoked"])
        self.assertEqual(res["diagnosis"]["category"], "TEST_REGRESSION")
        self.assertTrue(res["approval_gate"]["required"])
        self.assertEqual(res["cost_usd"], 0.0)

    def test_handle_contaminated_event_blocks(self):
        event = {
            "kind": "pipeline_failed",
            "project": "hg-stack-group/demo",
            "summary": "Bearer my_super_secret_token_12345678",
            "job_log": "Failure",
        }
        res = self.agent.handle_webhook_event(event)
        self.assertEqual(res["status"], "REJECTED_FAIL_CLOSED")
        self.assertFalse(res["agent_invoked"])
        self.assertIn("sensitive_data_in_event", res["reason"])

    def test_handle_invalid_kind_blocks(self):
        event = {
            "kind": "unknown_event_type",
            "project": "demo",
            "summary": "Random summary",
        }
        res = self.agent.handle_webhook_event(event)
        self.assertEqual(res["status"], "REJECTED_FAIL_CLOSED")
        self.assertIn("unsupported_event_kind", res["reason"])


if __name__ == "__main__":
    unittest.main()
