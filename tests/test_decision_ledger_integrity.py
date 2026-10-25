import unittest
from decision_ledger import DecisionLedger, DecisionEntry, compute_hash, canonical_json


class TestDecisionLedgerIntegrity(unittest.TestCase):
    """Comprehensive tests for deterministic cryptographic verification and tamper resistance."""

    def setUp(self):
        self.ledger = DecisionLedger()
        self.fixed_timestamp = 1700000000.0
        self.ledger.append("APPROVE_LOAN", {"applicant_id": 101, "amount": 50000}, timestamp=self.fixed_timestamp)
        self.ledger.append("REJECT_APPLICATION", {"applicant_id": 102, "reason": "fraud_score"}, timestamp=self.fixed_timestamp + 10)
        self.ledger.append("GRANT_PERMISSION", {"user": "admin", "role": "auditor"}, timestamp=self.fixed_timestamp + 20)

    def test_deterministic_immutability_and_chain_verification(self):
        """Test that a valid ledger verifies and produces deterministic root hashes across executions."""
        self.assertTrue(self.ledger.verify_integrity(), "Valid ledger should pass integrity check")
        self.assertEqual(len(self.ledger.entries), 3)
        self.assertEqual(self.ledger.entries[0].prev_hash, DecisionLedger.GENESIS_PREV_HASH)
        self.assertEqual(self.ledger.entries[1].prev_hash, self.ledger.entries[0].current_hash)
        self.assertEqual(self.ledger.entries[2].prev_hash, self.ledger.entries[1].current_hash)

        # Re-create identically to test determinism
        replica = DecisionLedger()
        replica.append("APPROVE_LOAN", {"applicant_id": 101, "amount": 50000}, timestamp=self.fixed_timestamp)
        replica.append("REJECT_APPLICATION", {"applicant_id": 102, "reason": "fraud_score"}, timestamp=self.fixed_timestamp + 10)
        replica.append("GRANT_PERMISSION", {"user": "admin", "role": "auditor"}, timestamp=self.fixed_timestamp + 20)

        self.assertEqual(self.ledger.get_merkle_root(), replica.get_merkle_root())
        for orig, rep in zip(self.ledger.entries, replica.entries):
            self.assertEqual(orig.current_hash, rep.current_hash)

    def test_tamper_detection_in_payload(self):
        """Test that any modification to an entry's payload fails cryptographic verification."""
        self.assertTrue(self.ledger.verify_integrity())

        # Tamper with the loan amount in the first entry
        self.ledger.entries[0].payload["amount"] = 9999999
        self.assertFalse(self.ledger.entries[0].verify(), "Entry self-verification should fail when payload is tampered")
        self.assertFalse(self.ledger.verify_integrity(), "Ledger integrity check should fail after payload alteration")

    def test_tamper_detection_in_hash_chain_linkage(self):
        """Test that altering linkage or swapping entries invalidates the ledger."""
        # Tamper by changing prev_hash of the middle entry
        tampered_hash = "a" * 64
        self.ledger.entries[1].prev_hash = tampered_hash
        self.assertFalse(self.ledger.verify_integrity(), "Ledger verification must fail when prev_hash is altered")

    def test_tamper_detection_entry_omission_or_reordering(self):
        """Test that deleting or reordering entries breaks the chain and index sequence."""
        # Drop the middle entry
        del self.ledger.entries[1]
        self.assertFalse(self.ledger.verify_integrity(), "Ledger verification must fail when an entry is omitted")

    def test_empty_ledger_integrity(self):
        """Test edge case of empty ledger."""
        empty_ledger = DecisionLedger()
        self.assertTrue(empty_ledger.verify_integrity())
        self.assertIsInstance(empty_ledger.get_merkle_root(), str)


if __name__ == "__main__":
    unittest.main()
