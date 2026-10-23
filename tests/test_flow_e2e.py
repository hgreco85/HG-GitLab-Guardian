"""End-to-End integration test of the autonomous post-code lifecycle flow."""
import json
import unittest
from pathlib import Path
from workflow_engine import WorkflowEngine
from metrics import get_comparative_metrics


class TestEndToEndFlow(unittest.TestCase):
    def setUp(self):
        self.engine = WorkflowEngine()
        self.fixtures_dir = Path(__file__).parent.parent / "fixtures"

    def test_e2e_assertion_failure_incident(self):
        with open(self.fixtures_dir / "incident_1_assertion_failure.json", "r", encoding="utf-8") as f:
            event = json.load(f)

        res = self.engine.run_lifecycle(event)
        self.assertTrue(res["success"])
        self.assertEqual(res["status"], "COMPLETED_READY_FOR_HUMAN_SIGN_OFF")
        self.assertEqual(res["diagnosis"]["category"], "TEST_REGRESSION")
        self.assertTrue(res["ledger_verified"])
        self.assertGreaterEqual(res["ledger_blocks_count"], 4)
        self.assertEqual(res["cost_usd"], 0.0)
        self.assertTrue(res["proposal"]["human_approval_required"])

    def test_e2e_security_advisory_incident(self):
        with open(self.fixtures_dir / "incident_2_security_advisory.json", "r", encoding="utf-8") as f:
            event = json.load(f)

        res = self.engine.run_lifecycle(event)
        self.assertTrue(res["success"])
        self.assertEqual(res["diagnosis"]["category"], "SECURITY_ADVISORY")
        self.assertIn("CVE-2026-3841", res["diagnosis"]["root_cause"])
        self.assertTrue(res["ledger_verified"])

    def test_e2e_secret_leak_blocked_fail_closed(self):
        with open(self.fixtures_dir / "incident_3_secret_leak_blocked.json", "r", encoding="utf-8") as f:
            event = json.load(f)

        res = self.engine.run_lifecycle(event)
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], "BLOCKED_FAIL_CLOSED")
        self.assertIn("sensitive_data_in_event", res["reason"])
        self.assertTrue(res["ledger_valid"])

    def test_comparative_metrics_structure(self):
        metrics = get_comparative_metrics()
        self.assertIn("empirical_measured_benchmark", metrics)
        self.assertIn("industry_comparative_estimates", metrics)
        emp = metrics["empirical_measured_benchmark"]["empirical_results"]
        self.assertEqual(emp["diagnostic_accuracy_pct"], 100.0)
        self.assertEqual(emp["secret_detection_accuracy_pct"], 100.0)
        ind = metrics["industry_comparative_estimates"]
        self.assertGreater(ind["mttr_minutes"]["estimated_reduction_pct"], 90.0)
        self.assertIn("$0.00", ind["marginal_cost"]["gitlab_guardian_measured"])


if __name__ == "__main__":
    unittest.main()
