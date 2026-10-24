import unittest
import hashlib
from sbom_verifier import (
    SBOMProvenanceVerifier,
    SBOMVerificationError,
    IntegrityMismatchError,
    ProvenanceError
)


class TestSBOMProvenanceVerifier(unittest.TestCase):
    def setUp(self):
        self.verifier = SBOMProvenanceVerifier(expected_author="SecOps Team", allowed_licenses=["Apache-2.0", "MIT"])
        self.sample_lib_data = b"def add(a, b): return a + b"
        self.sample_lib_sha256 = hashlib.sha256(self.sample_lib_data).hexdigest()

        self.valid_sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "metadata": {
                "authors": [{"name": "SecOps Team"}]
            },
            "components": [
                {
                    "name": "math-lib",
                    "version": "1.0.0",
                    "license": "MIT",
                    "hashes": {
                        "SHA-256": self.sample_lib_sha256
                    }
                }
            ]
        }

    def test_successful_verification(self):
        artifacts = {"math-lib": self.sample_lib_data}
        result = self.verifier.verify_sbom(self.valid_sbom, package_artifacts=artifacts)
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["total_verified"], 1)
        self.assertIn("math-lib", result["verified_components"])

    def test_sha256_integrity_tampering(self):
        tampered_data = b"def add(a, b): return a * b  # BACKDOOR"
        artifacts = {"math-lib": tampered_data}
        with self.assertRaises(IntegrityMismatchError):
            self.verifier.verify_sbom(self.valid_sbom, package_artifacts=artifacts)

    def test_provenance_unauthorized_author(self):
        tampered_sbom = dict(self.valid_sbom)
        tampered_sbom["metadata"] = {"authors": [{"name": "Unknown Attacker"}]}
        artifacts = {"math-lib": self.sample_lib_data}
        with self.assertRaises(ProvenanceError):
            self.verifier.verify_sbom(tampered_sbom, package_artifacts=artifacts)

    def test_license_compliance_violation(self):
        non_compliant_sbom = {
            "bomFormat": "CycloneDX",
            "metadata": {"authors": [{"name": "SecOps Team"}]},
            "components": [
                {
                    "name": "gpl-tool",
                    "version": "2.0.0",
                    "license": "GPL-3.0",
                    "hashes": {"SHA-256": self.sample_lib_sha256}
                }
            ]
        }
        with self.assertRaises(ProvenanceError):
            self.verifier.verify_sbom(non_compliant_sbom)

    def test_missing_hash_metadata(self):
        invalid_component = {
            "name": "unhashed-pkg",
            "version": "0.0.1",
            "license": "MIT",
            "hashes": {}
        }
        with self.assertRaises(ProvenanceError):
            self.verifier.verify_component(invalid_component)


if __name__ == "__main__":
    unittest.main()
