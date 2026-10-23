import unittest
from demo_three_incidents import demonstrate

class TestDemoThreeIncidents(unittest.TestCase):
    def test_three_scenarios(self):
        report = demonstrate()
        self.assertEqual(len(report["cases"]), 3)
        self.assertEqual([x["decision"] for x in report["cases"]],
                         ["MOCK_REVIEW", "MOCK_REVIEW", "BLOCK"])

    def test_security_never_reflects_secret(self):
        report = demonstrate()
        self.assertNotIn("SYNTHETIC_EXAMPLE_NOT_A_SECRET", str(report))
        self.assertEqual(report["cases"][2]["reason"], "sensitive_data")

    def test_never_executes(self):
        report = demonstrate()
        self.assertEqual(report["external_calls"], 0)
        self.assertEqual(report["cost_usd"], 0)
        self.assertFalse(report["real_gitlab_agent_used"])
        self.assertTrue(all(not x["agent_called"] and not x["allow_merge"]
                            and not x["allow_deploy"] for x in report["cases"]))
