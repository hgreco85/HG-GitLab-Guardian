import unittest
from submission_validator.manifest import SubmissionManifestAuditor, compute_bytes_sha256


class TestSubmissionManifestValidator(unittest.TestCase):
    def setUp(self):
        self.auditor = SubmissionManifestAuditor()
        self.file1_content = b"print('Hello, submission!')\n"
        self.file2_content = b"# Documentation file\n"
        self.hash1 = compute_bytes_sha256(self.file1_content)
        self.hash2 = compute_bytes_sha256(self.file2_content)
        self.virtual_fs = {
            "docs/README.md": self.file2_content,
            "src/main.py": self.file1_content,
        }

    def test_valid_manifest_passes_audit(self):
        manifest = {
            "checklist": {
                "license_verified": True,
                "artifacts_hashed": True,
                "documentation_included": True,
                "author_metadata_complete": True,
            },
            "license": {
                "spdx_identifier": "Apache-2.0",
                "holder": "Acme Corp",
                "year": 2026,
            },
            "artifacts": [
                {"path": "docs/README.md", "sha256": self.hash2},
                {"path": "src/main.py", "sha256": self.hash1},
            ],
        }
        result = self.auditor.audit_manifest(manifest, virtual_fs=self.virtual_fs)
        self.assertTrue(result["valid"])
        self.assertEqual(result["errors"], [])

    def test_checklist_validation_failures(self):
        incomplete_checklist = {
            "license_verified": True,
            "artifacts_hashed": False,
            # missing documentation_included and author_metadata_complete
        }
        errors = self.auditor.audit_checklist(incomplete_checklist)
        self.assertIn("Checklist item 'artifacts_hashed' must be True.", errors)
        self.assertIn("Missing required checklist item: 'documentation_included'.", errors)
        self.assertIn("Missing required checklist item: 'author_metadata_complete'.", errors)

    def test_license_metadata_validation(self):
        invalid_license = {
            "spdx_identifier": "Custom-Proprietary-1.0",
            "holder": "",
            "year": None,
        }
        errors = self.auditor.audit_license_metadata(invalid_license)
        self.assertTrue(any("approved canonical SPDX list" in err for err in errors))
        self.assertTrue(any("missing or empty 'holder'" in err for err in errors))
        self.assertTrue(any("missing 'year'" in err for err in errors))

    def test_artifact_integrity_and_ordering(self):
        # Test non-deterministic sorting detection
        unsorted_artifacts = [
            {"path": "src/main.py", "sha256": self.hash1},
            {"path": "docs/README.md", "sha256": self.hash2},
        ]
        errors = self.auditor.audit_artifact_integrity(unsorted_artifacts, virtual_fs=self.virtual_fs)
        self.assertIn("Artifacts manifest is not deterministically sorted by path.", errors)

        # Test hash mismatch and missing file
        corrupted_artifacts = [
            {"path": "docs/README.md", "sha256": "wronghashvalue1234567890"},
            {"path": "missing.txt", "sha256": self.hash1},
        ]
        errors_corrupt = self.auditor.audit_artifact_integrity(corrupted_artifacts, virtual_fs=self.virtual_fs)
        self.assertTrue(any("Integrity mismatch" in err for err in errors_corrupt))
        self.assertTrue(any("Artifact file not found in virtual filesystem" in err for err in errors_corrupt))


if __name__ == "__main__":
    unittest.main()
