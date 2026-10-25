import hashlib
import hmac
import json
import os
import tarfile
import zipfile
from typing import Any, Dict, List, Optional, Tuple


class AssetIntegrityError(Exception):
    """Raised when package asset integrity check fails."""
    pass


class AssetSignatureError(Exception):
    """Raised when package asset signature check fails."""
    pass


class PackageAssetAuditor:
    """
    Deterministic auditor for verifying package asset integrity and HMAC signatures.
    """

    def __init__(self, hash_algorithm: str = "sha256", secret_key: Optional[bytes] = None):
        if hash_algorithm not in hashlib.algorithms_available:
            raise ValueError(f"Unsupported hash algorithm: {hash_algorithm}")
        self.hash_algorithm = hash_algorithm
        self.secret_key = secret_key

    def _hash_bytes(self, data: bytes) -> str:
        h = hashlib.new(self.hash_algorithm)
        h.update(data)
        return h.hexdigest()

    def _sign_hash(self, content_hash: str) -> str:
        if not self.secret_key:
            raise AssetSignatureError("Secret key required for signing")
        mac = hmac.new(self.secret_key, content_hash.encode("utf-8"), self.hash_algorithm)
        return mac.hexdigest()

    def generate_manifest(self, asset_map: Dict[str, bytes]) -> Dict[str, Any]:
        """
        Deterministically generates an asset integrity manifest sorted by asset path.
        """
        sorted_paths = sorted(asset_map.keys())
        entries = []
        for path in sorted_paths:
            content = asset_map[path]
            content_hash = self._hash_bytes(content)
            entry = {
                "path": path,
                "size": len(content),
                "hash": content_hash,
            }
            if self.secret_key:
                entry["signature"] = self._sign_hash(content_hash)
            entries.append(entry)

        combined = ";".join(f"{e['path']}:{e['hash']}" for e in entries).encode("utf-8")
        package_digest = self._hash_bytes(combined)

        manifest = {
            "algorithm": self.hash_algorithm,
            "assets": entries,
            "package_digest": package_digest,
        }
        if self.secret_key:
            manifest["package_signature"] = self._sign_hash(package_digest)

        return manifest

    def audit_assets(self, asset_map: Dict[str, bytes], manifest: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Audits an asset map against a reference manifest.
        """
        errors: List[str] = []
        expected_assets = {e["path"]: e for e in manifest.get("assets", [])}

        if manifest.get("algorithm") != self.hash_algorithm:
            errors.append(f"Algorithm mismatch: expected {self.hash_algorithm}, got {manifest.get('algorithm')}")

        for path, exp in expected_assets.items():
            if path not in asset_map:
                errors.append(f"Missing asset: {path}")
                continue
            actual_content = asset_map[path]
            if len(actual_content) != exp.get("size"):
                errors.append(f"Size mismatch for {path}: expected {exp.get('size')}, got {len(actual_content)}")
            actual_hash = self._hash_bytes(actual_content)
            if actual_hash != exp.get("hash"):
                errors.append(f"Hash mismatch for {path}")

            if self.secret_key and "signature" in exp:
                expected_sig = self._sign_hash(exp["hash"])
                if not hmac.compare_digest(exp["signature"], expected_sig):
                    errors.append(f"Invalid signature for asset: {path}")

        for path in asset_map:
            if path not in expected_assets:
                errors.append(f"Unexpected extra asset: {path}")

        sorted_paths = sorted(asset_map.keys())
        combined = ";".join(f"{p}:{self._hash_bytes(asset_map[p])}" for p in sorted_paths).encode("utf-8")
        calc_digest = self._hash_bytes(combined)
        if calc_digest != manifest.get("package_digest"):
            errors.append("Package digest mismatch")

        if self.secret_key and "package_signature" in manifest:
            expected_pkg_sig = self._sign_hash(manifest["package_digest"])
            if not hmac.compare_digest(manifest["package_signature"], expected_pkg_sig):
                errors.append("Invalid package signature")

        return (len(errors) == 0, errors)

    def audit_archive(self, archive_path: str, manifest: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Reads a zip or tar archive and audits its contents against the manifest.
        """
        asset_map: Dict[str, bytes] = {}
        if zipfile.is_zipfile(archive_path):
            with zipfile.ZipFile(archive_path, "r") as zf:
                for name in zf.namelist():
                    if not name.endswith("/"):
                        asset_map[name] = zf.read(name)
        elif tarfile.is_tarfile(archive_path):
            with tarfile.open(archive_path, "r:*") as tf:
                for member in tf.getmembers():
                    if member.isfile():
                        extracted = tf.extractfile(member)
                        asset_map[member.name] = extracted.read() if extracted else b""
        else:
            return False, [f"Unsupported archive format: {archive_path}"]

        return self.audit_assets(asset_map, manifest)
