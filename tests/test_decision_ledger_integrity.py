"""Deterministic cryptographic verification of decision ledger immutability and tamper resistance.

GitLab Transcend Hackathon - Life After Code.
Offline deterministic unittest suite, zero network, USD 0.00.
"""

import hashlib
import json
import unittest
from pathlib import Path
from ledger import DecisionBlock, DecisionLedger


class TestDecisionLedgerCryptographicIntegrity(unittest.TestCase):
    def test_block_hash_computation_deterministic(self):
        b1 = DecisionBlock(
            index=0,
            timestamp=1700000000.0,
            step="TRIAGE",
            actor="GitLabDuoAgent",
            action="DIAGNOSE_INCIDENT",
            payload={"incident_id": "INC-01", "root_cause": "OOMKilled"},
            previous_hash="0" * 64,
        )
        expected_hash = b1.compute_hash()
        self.assertEqual(b1.hash, expected_hash)
        self.assertEqual(len(b1.hash), 64)

    def test_tamper_detection_in_block_payload(self):
        b1 = DecisionBlock(
            index=1,
            timestamp=1700000010.0,
            step="REMEDIATION",
            actor="GitLabGuardian",
            action="ROLLBACK_MR",
            payload={"mr_iid": 42, "approved": True},
            previous_hash="0" * 64,
        )
        original_hash = b1.hash
        b1.payload["approved"] = False
        recomputed_hash = b1.compute_hash()
        self.assertNotEqual(original_hash, recomputed_hash)

    def test_ledger_append_and_verify_chain(self):
        ledger = DecisionLedger()
        self.assertEqual(len(ledger.chain), 1)  # Genesis
        b0 = ledger.record(
            step="INIT",
            actor="System",
            action="BOOT",
            payload={"status": "ready"},
        )
        b1 = ledger.record(
            step="EVALUATE",
            actor="DuoAgent",
            action="ANALYZE_PIPELINE",
            payload={"pipeline_id": 999},
        )
        self.assertEqual(len(ledger.chain), 3)
        self.assertEqual(b1.previous_hash, b0.hash)
        self.assertTrue(ledger.verify())

    def test_ledger_detects_chain_corruption(self):
        ledger = DecisionLedger()
        ledger.record(step="A", actor="Agent", action="ACT_A", payload={})
        ledger.record(step="B", actor="Agent", action="ACT_B", payload={})
        ledger.chain[2].previous_hash = "corrupted_hash"
        self.assertFalse(ledger.verify())

    def test_block_to_dict_preserves_schema(self):
        ledger = DecisionLedger()
        blk = ledger.record(step="STEP_1", actor="AgentX", action="ACTION_Y", payload={"key": "val"})
        d = blk.to_dict()
        self.assertIn("index", d)
        self.assertIn("timestamp", d)
        self.assertIn("step", d)
        self.assertIn("hash", d)
        self.assertEqual(d["payload"]["key"], "val")


if __name__ == "__main__":
    unittest.main()
