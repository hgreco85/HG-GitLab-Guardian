import unittest
from benchmark import evaluate
from mock_agent import simulate

class TestMockBenchmark(unittest.TestCase):
    def test_all_synthetic_scenarios(self):
        report = evaluate()
        self.assertEqual(report["scenarios"], 8)
        self.assertEqual(report["failed"], 0)

    def test_no_real_agent_or_billing(self):
        result = simulate({"kind": "test_failed", "summary": "assert mismatch"})
        self.assertIs(result["agent_called"], False)
        self.assertEqual(result["billing_calls"], 0)
        self.assertIs(result["allow_merge"], False)
        self.assertIs(result["allow_deploy"], False)

    def test_invalid_event_never_invokes_agent(self):
        result = simulate({"kind": "test_failed", "summary": "token=xyz"})
        self.assertEqual(result["status"], "BLOCK")
        self.assertIs(result["agent_called"], False)
