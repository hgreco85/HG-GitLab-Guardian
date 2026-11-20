import hashlib
import hmac
import json
import os
from typing import Dict, List, Optional, Tuple


class AssetIntegrityAuditor:
    """
    Deterministic package asset integrity and signature auditor.
    Verifies file checksums (SHA256) and HMAC signatures deterministically.
    """

    def __init__(self, secret_key: Optional[bytes] = None, hash_algorithm: str = 'sha256'):
        self.secret_key = secret_key
        self.hash_algorithm = hash_algorithm.lower()

    def compute_file_hash(self, file_path: str) -> str:
        """Computes deterministic digest of a file content."""
        hasher = hashlib.new(self.hash_algorithm)
        with open(file_path, 'rb') as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def compute_signature(self, manifest_data: bytes) -> str:
        """Computes HMAC signature for normalized manifest bytes."""
        if not self.secret_key:
            raise ValueError("Secret key required to compute or verify signatures.")
        return hmac.new(self.secret_key, manifest_data, hashlib.sha256).hexdigest()

    def generate_manifest(self, root_dir: str, exclude_files: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Generates a deterministic sorted mapping of relative POSIX path -> hex digest.
        """
        exclude = set(exclude_files or [])
        manifest: Dict[str, str] = {}

        for dirpath, _, filenames in sorted(os.walk(root_dir)):
            for fname in sorted(filenames):
                rel_path = os.path.relpath(os.path.join(dirpath, fname), root_dir).replace('\\', '/')
                if rel_path in exclude:
                    continue
                full_path = os.path.join(dirpath, fname)
                manifest[rel_path] = self.compute_file_hash(full_path)

        return dict(sorted(manifest.items()))

    def serialize_manifest(self, manifest: Dict[str, str]) -> bytes:
        """Serializes manifest deterministically (canonical JSON: sorted keys, compact separators)."""
        canonical_json = json.dumps(manifest, sort_keys=True, separators=(',', ':'))
        return canonical_json.encode('utf-8')

    def export_package_audit(self, root_dir: str, output_manifest_path: str, output_sig_path: Optional[str] = None) -> None:
        """Generates manifest and optional signature file for a directory."""
        exclude = []
        rel_out = os.path.relpath(output_manifest_path, root_dir).replace('\\', '/')
        exclude.append(rel_out)
        if output_sig_path:
            rel_sig = os.path.relpath(output_sig_path, root_dir).replace('\\', '/')
            exclude.append(rel_sig)

        manifest = self.generate_manifest(root_dir, exclude_files=exclude)
        manifest_bytes = self.serialize_manifest(manifest)

        with open(output_manifest_path, 'wb') as f:
            f.write(manifest_bytes)

        if output_sig_path:
            sig = self.compute_signature(manifest_bytes)
            with open(output_sig_path, 'w', encoding='utf-8') as f:
                f.write(sig)

    def audit_package(
        self,
        root_dir: str,
        manifest_path: str,
        signature_path: Optional[str] = None
    ) -> Tuple[bool, List[str]]:
        """
        Audits assets in root_dir against manifest and optional signature.
        Returns (is_valid, list_of_errors).
        """
        errors: List[str] = []

        if not os.path.exists(manifest_path):
            return False, [f"Manifest not found: {manifest_path}"]

        with open(manifest_path, 'rb') as f:
            manifest_bytes = f.read()

        # Signature verification if signature file is provided
        if signature_path is not None:
            if not os.path.exists(signature_path):
                return False, [f"Signature file not found: {signature_path}"]
            with open(signature_path, 'r', encoding='utf-8') as f:
                expected_sig = f.read().strip()
            try:
                computed_sig = self.compute_signature(manifest_bytes)
                if not hmac.compare_digest(expected_sig, computed_sig):
                    errors.append("Signature mismatch: manifest integrity verification failed.")
            except Exception as e:
                errors.append(f"Signature verification error: {str(e)}")

        try:
            expected_manifest = json.loads(manifest_bytes.decode('utf-8'))
        except Exception as e:
            return False, [f"Malformed manifest JSON: {str(e)}"]

        exclude = [
            os.path.relpath(manifest_path, root_dir).replace('\\', '/')
        ]
        if signature_path:
            exclude.append(os.path.relpath(signature_path, root_dir).replace('\\', '/'))

        actual_manifest = self.generate_manifest(root_dir, exclude_files=exclude)

        # Check missing or modified files
        for path, exp_hash in expected_manifest.items():
            if path not in actual_manifest:
                errors.append(f"Missing asset: {path}")
            elif actual_manifest[path] != exp_hash:
                errors.append(f"Integrity check failed for {path}: expected {exp_hash}, got {actual_manifest[path]}")

        # Check extra untracked files
        for path in actual_manifest:
            if path not in expected_manifest:
                errors.append(f"Unexpected untracked asset found: {path}")

        return len(errors) == 0, errors
