import hashlib
import os
import shutil
import tempfile
import unittest

from submission_manifest_validator import (
    audit_artifact_integrity,
    audit_checklist,
    audit_license_metadata,
    calculate_file_hash,
)


class TestSubmissionManifestValidator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_checklist_auditor_complete_and_missing(self):
        complete_manifest = [
            "README.md",
            "LICENSE",
            "metadata.json",
            "src/module.py",
            "tests/test_module.py",
        ]
        is_valid, missing = audit_checklist(complete_manifest)
        self.assertTrue(is_valid)
        self.assertEqual(missing, [])

        incomplete_manifest = [
            "README.md",
            "src/main.py",
        ]
        is_valid, missing = audit_checklist(incomplete_manifest)
        self.assertFalse(is_valid)
        self.assertIn("LICENSE", missing)
        self.assertIn("metadata.json", missing)
        self.assertIn("tests/", missing)

    def test_license_metadata_auditor(self):
        valid, msg = audit_license_metadata("MIT", "Copyright (c) 2026 MIT License details...")
        self.assertTrue(valid)
        self.assertIn("valid", msg)

        invalid, msg = audit_license_metadata("UNKNOWN-LICENSE", "Some content")
        self.assertFalse(invalid)
        self.assertIn("Invalid or unrecognized", msg)

        mismatched_content, msg = audit_license_metadata("Apache-2.0", "This is a completely different proprietary text")
        self.assertFalse(mismatched_content)
        self.assertIn("does not match expected", msg)

    def test_artifact_integrity_auditor(self):
        file1_path = os.path.join(self.test_dir, "artifact1.txt")
        file2_path = os.path.join(self.test_dir, "artifact2.bin")

        content1 = b"Deterministic artifact content 1"
        content2 = b"Deterministic artifact content 2"

        with open(file1_path, "wb") as f:
            f.write(content1)
        with open(file2_path, "wb") as f:
            f.write(content2)

        hash1 = hashlib.sha256(content1).hexdigest()
        hash2 = hashlib.sha256(content2).hexdigest()

        manifest_checksums = {
            "artifact1.txt": hash1,
            "artifact2.bin": hash2,
        }

        is_valid, mismatches = audit_artifact_integrity(manifest_checksums, base_dir=self.test_dir)
        self.assertTrue(is_valid)
        self.assertEqual(mismatches, [])

        tampered_manifest = {
            "artifact1.txt": hash1,
            "artifact2.bin": "0" * 64,
            "non_existent.txt": hash1,
        }
        is_valid, mismatches = audit_artifact_integrity(tampered_manifest, base_dir=self.test_dir)
        self.assertFalse(is_valid)
        self.assertEqual(len(mismatches), 2)
        self.assertTrue(any("Hash mismatch for artifact2.bin" in m for m in mismatches))
        self.assertTrue(any("Missing file: non_existent.txt" in m for m in mismatches))


if __name__ == "__main__":
    unittest.main()
