"""Offline deterministic tests: execute with python -m unittest discover -s tools/gitlab_guardian -p 'test_*.py'."""
import unittest
from guardian import assess


class TestGuardian(unittest.TestCase):
    def test_missing(self):
        self.assertEqual(assess({})["reason"], "missing_evidence")

    def test_known_state(self):
        data = dict(seat_assigned=True, community_role="Developer", agent_platform_enabled=False,
                    credit_balance_verified=False, zero_cost_guaranteed=False, runner_explicitly_enabled=False)
        self.assertEqual(assess(data)["reason"], "agent_platform_unverified")

    def test_paid_block(self):
        data = dict(seat_assigned=True, community_role="Developer", agent_platform_enabled=True,
                    credit_balance_verified=True, zero_cost_guaranteed=False, runner_explicitly_enabled=True)
        self.assertEqual(assess(data)["reason"], "cost_unverified")

    def test_router_block(self):
        data = dict(seat_assigned=True, community_role="Developer", agent_platform_enabled=True,
                    credit_balance_verified=True, zero_cost_guaranteed=True, runner_explicitly_enabled=False)
        self.assertEqual(assess(data)["reason"], "execution_router_disabled")

    def test_all_attestations_still_no_execution(self):
        data = dict(seat_assigned=True, community_role="Developer", agent_platform_enabled=True,
                    credit_balance_verified=True, zero_cost_guaranteed=True, runner_explicitly_enabled=True)
        self.assertFalse(assess(data)["may_execute"])

    def test_invalid_role(self):
        data = dict(seat_assigned=True, community_role="Guest", agent_platform_enabled=True,
                    credit_balance_verified=True, zero_cost_guaranteed=True, runner_explicitly_enabled=True)
        self.assertEqual(assess(data)["reason"], "no_valid_access")

    def test_type_confusion_fails_closed(self):
        data = dict(seat_assigned="true", community_role="Developer", agent_platform_enabled=True,
                    credit_balance_verified=True, zero_cost_guaranteed=True, runner_explicitly_enabled=True)
        self.assertEqual(assess(data)["reason"], "no_valid_access")

    def test_non_dict_fails_closed(self):
        self.assertFalse(assess([])["may_execute"])


if __name__ == "__main__":
    unittest.main()
