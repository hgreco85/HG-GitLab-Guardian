import unittest
from transcend_v2 import triage

class TestTranscendV2(unittest.TestCase):
    def test_event_draft_only(self):
        r = triage({"kind": "pipeline_failed", "project": "demo", "summary": "unit failed"})
        self.assertEqual(r["status"], "DRAFT_REVIEW_ONLY")
        self.assertIs(r["allow_agent"], False)
        self.assertIs(r["allow_deploy"], False)
    def test_unknown_event_blocks(self):
        self.assertEqual(triage({"kind": "transfer_funds", "summary": "x"})["status"], "BLOCK")
    def test_secrets_block(self):
        self.assertEqual(triage({"kind": "test_failed", "summary": "secret=abc"})["reason"], "sensitive_data")
    def test_unexpected_fields_block(self):
        self.assertEqual(triage({"kind": "test_failed", "summary": "x", "command": "run"})["reason"], "invalid_event")

    def test_unhashable_kind_fails_closed(self):
        self.assertEqual(triage({"kind": [], "summary": "x"})["reason"], "invalid_event")

    def test_kind_mapping_fails_closed(self):
        self.assertEqual(triage({"kind": {"oops": 1}, "summary": "x"})["reason"], "invalid_event")

    def test_missing_summary_fails_closed(self):
        self.assertEqual(triage({"kind": "pipeline_failed"})["reason"], "invalid_event")
