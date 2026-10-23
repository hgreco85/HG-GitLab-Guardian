"""Deterministic adversarial regression suite. No network or provider calls."""
import random
import unittest
from transcend_v2 import triage
from mock_agent import simulate

class TestSecurityHardening(unittest.TestCase):
    def test_seeded_fuzz_no_exception_or_execution(self):
        rng = random.Random(1407)
        bad = [None, 0, 3.2, [], {}, True, (1,), {"x": 4}]
        for _ in range(500):
            event = rng.choice(bad + [
                {"kind": rng.choice(bad), "summary": "ok"},
                {"kind": "test_failed", "summary": rng.choice(bad)},
                {"kind": "pipeline_failed", "summary": "normal", "url": rng.choice(bad)},
            ])
            with self.subTest(event=repr(event)):
                outcome = triage(event)
                self.assertEqual(outcome["status"], "BLOCK")
                self.assertFalse(outcome.get("allow_agent", False))
                self.assertFalse(outcome.get("allow_deploy", False))
                self.assertFalse(outcome.get("allow_merge", False))

    def test_no_secret_reflection(self):
        for secret in ("Authorization: Bearer abc123", "glpat-abc123", "api-key=abc", "private_key=abc", "sk-abcdef"):
            with self.subTest(secret=secret):
                outcome = triage({"kind": "test_failed", "summary": secret})
                self.assertEqual(outcome["reason"], "sensitive_data")
                self.assertNotIn(secret, str(outcome))

    def test_non_string_optional_fields(self):
        for field in ("project", "url"):
            self.assertEqual(triage({"kind": "test_failed", "summary": "ok", field: []})["reason"], "invalid_event")

    def test_size_limit(self):
        self.assertEqual(triage({"kind": "test_failed", "summary": "a" * 2049})["reason"], "invalid_event")

    def test_mock_stays_unprivileged(self):
        result = simulate({"kind": "security_alert", "summary": "dependency review"})
        self.assertFalse(result["agent_called"])
        self.assertEqual(result["billing_calls"], 0)
