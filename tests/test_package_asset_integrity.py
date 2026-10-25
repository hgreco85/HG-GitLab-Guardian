import os
import tempfile
import unittest
import zipfile
from package_auditor import PackageAssetAuditor, AssetIntegrityError, AssetSignatureError


class TestPackageAssetIntegrity(unittest.TestCase):
    def setUp(self):
        self.secret = b"deterministic-test-secret-key-32b!"
        self.auditor = PackageAssetAuditor(hash_algorithm="sha256", secret_key=self.secret)
        self.assets = {
            "data/file1.txt": b"Hello World! Deterministic asset test.",
            "bin/executable": b"\x7fELF\x02\x01\x01\x00",
            "README.md": b"# Package Documentation\nVerified package content.",
        }

    def test_deterministic_manifest_generation(self):
        manifest1 = self.auditor.generate_manifest(self.assets)
        manifest2 = self.auditor.generate_manifest(self.assets)
        self.assertEqual(manifest1, manifest2)
        self.assertEqual(manifest1["algorithm"], "sha256")
        self.assertIn("package_digest", manifest1)
        self.assertIn("package_signature", manifest1)
        self.assertEqual(len(manifest1["assets"]), 3)
        self.assertEqual([entry["path"] for entry in manifest1["assets"]], sorted(self.assets.keys()))

    def test_audit_success(self):
        manifest = self.auditor.generate_manifest(self.assets)
        valid, errors = self.auditor.audit_assets(self.assets, manifest)
        self.assertTrue(valid)
        self.assertEqual(len(errors), 0)

    def test_tampered_asset_hash_failure(self):
        manifest = self.auditor.generate_manifest(self.assets)
        tampered_assets = dict(self.assets)
        tampered_assets["README.md"] = b"Tampered README content!"
        valid, errors = self.auditor.audit_assets(tampered_assets, manifest)
        self.assertFalse(valid)
        self.assertTrue(any("Hash mismatch for README.md" in err for err in errors))
        self.assertTrue(any("Package digest mismatch" in err for err in errors))

    def test_missing_and_unexpected_assets(self):
        manifest = self.auditor.generate_manifest(self.assets)
        modified_assets = dict(self.assets)
        del modified_assets["bin/executable"]
        modified_assets["extra/untracked.bin"] = b"rogue asset"
        valid, errors = self.auditor.audit_assets(modified_assets, manifest)
        self.assertFalse(valid)
        self.assertTrue(any("Missing asset: bin/executable" in err for err in errors))
        self.assertTrue(any("Unexpected extra asset: extra/untracked.bin" in err for err in errors))

    def test_tampered_signature_failure(self):
        manifest = self.auditor.generate_manifest(self.assets)
        manifest["assets"][0]["signature"] = "0" * 64
        valid, errors = self.auditor.audit_assets(self.assets, manifest)
        self.assertFalse(valid)
        self.assertTrue(any("Invalid signature for asset:" in err for err in errors))

    def test_tampered_package_signature_failure(self):
        manifest = self.auditor.generate_manifest(self.assets)
        manifest["package_signature"] = "0" * 64
        valid, errors = self.auditor.audit_assets(self.assets, manifest)
        self.assertFalse(valid)
        self.assertTrue(any("Invalid package signature" in err for err in errors))

    def test_zip_archive_audit(self):
        manifest = self.auditor.generate_manifest(self.assets)
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            zip_path = f.name
        try:
            with zipfile.ZipFile(zip_path, "w") as zf:
                for path, data in self.assets.items():
                    zf.writestr(path, data)
            valid, errors = self.auditor.audit_archive(zip_path, manifest)
            self.assertTrue(valid)
            self.assertEqual(errors, [])
        finally:
            if os.path.exists(zip_path):
                os.remove(zip_path)

    def test_unsupported_hash_algorithm(self):
        with self.assertRaises(ValueError):
            PackageAssetAuditor(hash_algorithm="unknown_nonexistent_hash_algo")

    def test_unsigned_mode(self):
        unsigned_auditor = PackageAssetAuditor(hash_algorithm="sha256", secret_key=None)
        manifest = unsigned_auditor.generate_manifest(self.assets)
        self.assertNotIn("package_signature", manifest)
        self.assertNotIn("signature", manifest["assets"][0])
        valid, errors = unsigned_auditor.audit_assets(self.assets, manifest)
        self.assertTrue(valid)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
