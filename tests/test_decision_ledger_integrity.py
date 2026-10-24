import unittest
from decision_ledger import DecisionLedger, DecisionLedgerBlock


class TestDecisionLedgerIntegrity(unittest.TestCase):
    def setUp(self):
        self.ledger = DecisionLedger()
        self.ledger.initialize_genesis(genesis_decision={"action": "INITIALIZE", "actor": "system"}, timestamp=1700000000.0)
        self.ledger.record_decision(
            decision={"action": "APPROVE_LOAN", "applicant_id": 101, "amount": 5000},
            timestamp=1700000010.0,
        )
        self.ledger.record_decision(
            decision={"action": "DEPLOY_MODEL", "model_version": "v1.0.4"},
            timestamp=1700000020.0,
        )

    def test_ledger_valid_integrity_and_determinism(self):
        """Verify that an untampered ledger is cryptographically valid and deterministic."""
        self.assertTrue(self.ledger.verify_integrity())
        self.assertEqual(len(self.ledger.chain), 3)

        # Re-verify deterministic recalculation of all block hashes
        for block in self.ledger.chain:
            self.assertEqual(block.hash, block.calculate_hash())

        exported = self.ledger.export_ledger()
        reloaded_ledger = DecisionLedger.load_ledger(exported)
        self.assertTrue(reloaded_ledger.verify_integrity())
        self.assertEqual(reloaded_ledger.chain[-1].hash, self.ledger.chain[-1].hash)

    def test_tamper_decision_payload_detected(self):
        """Ensure tampering with decision content breaks cryptographic integrity."""
        self.assertTrue(self.ledger.verify_integrity())

        # Tamper with the loan amount in block 1
        self.ledger.chain[1].decision["amount"] = 50000

        # Integrity check must fail because calculate_hash() no longer matches block.hash
        self.assertFalse(self.ledger.verify_integrity())

    def test_tamper_hash_chain_linkage_detected(self):
        """Ensure changing previous_hash or block ordering breaks cryptographic linkage."""
        # If an attacker recomputes block 1's hash after tampering
        self.ledger.chain[1].decision["amount"] = 99999
        self.ledger.chain[1].hash = self.ledger.chain[1].calculate_hash()

        # Now block 1's internal hash matches, but block 2's previous_hash won't match block 1's new hash
        self.assertFalse(self.ledger.verify_integrity())

    def test_tamper_genesis_block_detected(self):
        """Ensure tampering with genesis block index, previous hash, or content is detected."""
        # Tamper genesis previous hash
        self.ledger.chain[0].previous_hash = "1" * 64
        self.assertFalse(self.ledger.verify_integrity())


if __name__ == "__main__":
    unittest.main()
