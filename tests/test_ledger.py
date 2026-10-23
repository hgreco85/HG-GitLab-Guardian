"""Unit tests for cryptographic decision ledger."""
import unittest
from ledger import DecisionLedger


class TestDecisionLedger(unittest.TestCase):
    def setUp(self):
        self.ledger = DecisionLedger()

    def test_genesis_block_initialized(self):
        self.assertEqual(len(self.ledger.chain), 1)
        self.assertEqual(self.ledger.chain[0].step, "GENESIS")
        self.assertTrue(self.ledger.verify())

    def test_record_multiple_blocks(self):
        b1 = self.ledger.record("1_INGEST", "SYSTEM", "INGEST_EVENT", {"id": 1})
        b2 = self.ledger.record("2_TRIAGE", "AGENT", "DIAGNOSE", {"category": "TEST_REGRESSION"})
        self.assertEqual(len(self.ledger.chain), 3)
        self.assertEqual(b2.previous_hash, b1.hash)
        self.assertTrue(self.ledger.verify())

    def test_tamper_detection(self):
        self.ledger.record("1_INGEST", "SYSTEM", "INGEST_EVENT", {"id": 1})
        self.ledger.record("2_TRIAGE", "AGENT", "DIAGNOSE", {"category": "TEST_REGRESSION"})
        # Tamper with block payload
        self.ledger.chain[1].payload["tampered"] = True
        self.assertFalse(self.ledger.verify())

    def test_export_structure(self):
        self.ledger.record("STEP", "ACTOR", "ACTION", {"key": "val"})
        exported = self.ledger.export()
        self.assertEqual(len(exported), 2)
        self.assertIn("hash", exported[1])
        self.assertIn("previous_hash", exported[1])


if __name__ == "__main__":
    unittest.main()
