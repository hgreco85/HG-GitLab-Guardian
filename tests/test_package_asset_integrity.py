import json
import os
import shutil
import tempfile
import unittest
from asset_integrity_auditor import AssetIntegrityAuditor


class TestPackageAssetIntegrityAuditor(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.secret_key = b"deterministic_super_secret_audit_key_32bytes!"
        self.auditor = AssetIntegrityAuditor(secret_key=self.secret_key)

        # Setup mock package assets
        self.assets_dir = os.path.join(self.test_dir, "package")
        os.makedirs(os.path.join(self.assets_dir, "sub"), exist_ok=True)

        self.file_a = os.path.join(self.assets_dir, "file_a.txt")
        with open(self.file_a, "w", encoding="utf-8") as f:
            f.write("Hello World Package Asset A")

        self.file_b = os.path.join(self.assets_dir, "sub", "binary.bin")
        with open(self.file_b, "wb") as f:
            f.write(b"\x00\x01\x02\x03binary_data")

        self.manifest_file = os.path.join(self.assets_dir, "assets_manifest.json")
        self.sig_file = os.path.join(self.assets_dir, "assets_manifest.sig")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_audit_valid_package_success(self):
        """Test that an unmodified package passes integrity and signature audit."""
        self.auditor.export_package_audit(self.assets_dir, self.manifest_file, self.sig_file)

        is_valid, errors = self.auditor.audit_package(
            root_dir=self.assets_dir,
            manifest_path=self.manifest_file,
            signature_path=self.sig_file
        )
        self.assertTrue(is_valid, f"Expected valid audit but failed with errors: {errors}")
        self.assertEqual(errors, [])

    def test_audit_detects_tampered_asset(self):
        """Test that modifying an asset detects checksum failure."""
        self.auditor.export_package_audit(self.assets_dir, self.manifest_file, self.sig_file)

        # Tamper with file_a.txt
        with open(self.file_a, "a", encoding="utf-8") as f:
            f.write("tampered_payload")

        is_valid, errors = self.auditor.audit_package(
            root_dir=self.assets_dir,
            manifest_path=self.manifest_file,
            signature_path=self.sig_file
        )
        self.assertFalse(is_valid)
        self.assertTrue(any("Integrity check failed for file_a.txt" in err for err in errors))

    def test_audit_detects_untracked_and_missing_assets(self):
        """Test detection of missing assets and unexpected extraneous assets."""
        self.auditor.export_package_audit(self.assets_dir, self.manifest_file, self.sig_file)

        # Add unexpected file
        extra_file = os.path.join(self.assets_dir, "unauthorized.txt")
        with open(extra_file, "w", encoding="utf-8") as f:
            f.write("injected untracked file")

        # Remove genuine file
        os.remove(self.file_b)

        is_valid, errors = self.auditor.audit_package(
            root_dir=self.assets_dir,
            manifest_path=self.manifest_file,
            signature_path=self.sig_file
        )
        self.assertFalse(is_valid)
        self.assertTrue(any("Missing asset: sub/binary.bin" in err for err in errors))
        self.assertTrue(any("Unexpected untracked asset found: unauthorized.txt" in err for err in errors))

    def test_audit_detects_invalid_or_tampered_signature(self):
        """Test that tampering with the signature file triggers audit rejection."""
        self.auditor.export_package_audit(self.assets_dir, self.manifest_file, self.sig_file)

        with open(self.sig_file, "w", encoding="utf-8") as f:
            f.write("bad_fake_signature_hash")

        is_valid, errors = self.auditor.audit_package(
            root_dir=self.assets_dir,
            manifest_path=self.manifest_file,
            signature_path=self.sig_file
        )
        self.assertFalse(is_valid)
        self.assertTrue(any("Signature mismatch" in err for err in errors))

    def test_deterministic_manifest_order(self):
        """Test that manifest generation and serialization is strictly deterministic."""
        manifest1 = self.auditor.generate_manifest(self.assets_dir)
        bytes1 = self.auditor.serialize_manifest(manifest1)

        manifest2 = self.auditor.generate_manifest(self.assets_dir)
        bytes2 = self.auditor.serialize_manifest(manifest2)

        self.assertEqual(bytes1, bytes2)
        parsed = json.loads(bytes1.decode('utf-8'))
        self.assertIn("file_a.txt", parsed)
        self.assertIn("sub/binary.bin", parsed)


if __name__ == '__main__':
    unittest.main()
