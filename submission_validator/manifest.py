import hashlib
import os
from typing import Any, Dict, List, Optional


SPDX_CANONICAL_LICENSES = {
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "GPL-3.0-only",
    "ISC",
}

REQUIRED_CHECKLIST_ITEMS = [
    "license_verified",
    "artifacts_hashed",
    "documentation_included",
    "author_metadata_complete",
]


def compute_sha256(filepath: str, chunk_size: int = 65536) -> str:
    """Compute deterministic SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_bytes_sha256(data: bytes) -> str:
    """Compute SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()


class SubmissionManifestAuditor:
    """
    Auditor for deterministic submission package checklist, license metadata,
    and artifact integrity verification.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or "."

    def audit_checklist(self, checklist: Dict[str, Any]) -> List[str]:
        """
        Verifies that all required checklist items are present and evaluate to True.
        """
        errors = []
        for item in REQUIRED_CHECKLIST_ITEMS:
            if item not in checklist:
                errors.append(f"Missing required checklist item: '{item}'.")
            elif not bool(checklist[item]):
                errors.append(f"Checklist item '{item}' must be True.")
        return errors

    def audit_license_metadata(self, license_meta: Dict[str, Any]) -> List[str]:
        """
        Verifies license identifier, copyright holder, and license file presence.
        """
        errors = []
        spdx_id = license_meta.get("spdx_identifier")
        if not spdx_id:
            errors.append("License metadata missing 'spdx_identifier'.")
        elif spdx_id not in SPDX_CANONICAL_LICENSES:
            errors.append(f"License identifier '{spdx_id}' is not in approved canonical SPDX list.")

        if not license_meta.get("holder") or not str(license_meta.get("holder")).strip():
            errors.append("License metadata missing or empty 'holder'.")

        if not license_meta.get("year"):
            errors.append("License metadata missing 'year'.")

        return errors

    def audit_artifact_integrity(
        self, artifacts: List[Dict[str, str]], virtual_fs: Optional[Dict[str, bytes]] = None
    ) -> List[str]:
        """
        Verifies that each listed artifact matches its expected SHA-256 digest.
        Artifacts must be sorted deterministically by path in the manifest.
        """
        errors = []
        if not artifacts:
            errors.append("No artifacts provided for audit.")
            return errors

        paths = [item.get("path", "") for item in artifacts]
        if paths != sorted(paths):
            errors.append("Artifacts manifest is not deterministically sorted by path.")

        for item in artifacts:
            rel_path = item.get("path")
            expected_hash = item.get("sha256")

            if not rel_path or not expected_hash:
                errors.append(f"Artifact entry malformed: {item}")
                continue

            if virtual_fs is not None:
                if rel_path not in virtual_fs:
                    errors.append(f"Artifact file not found in virtual filesystem: '{rel_path}'.")
                    continue
                actual_hash = compute_bytes_sha256(virtual_fs[rel_path])
            else:
                full_path = os.path.join(self.base_dir, rel_path)
                if not os.path.exists(full_path):
                    errors.append(f"Artifact file not found: '{rel_path}'.")
                    continue
                actual_hash = compute_sha256(full_path)

            if actual_hash.lower() != expected_hash.lower():
                errors.append(
                    f"Integrity mismatch for '{rel_path}': expected {expected_hash}, got {actual_hash}."
                )

        return errors

    def audit_manifest(
        self, manifest: Dict[str, Any], virtual_fs: Optional[Dict[str, bytes]] = None
    ) -> Dict[str, Any]:
        """
        Runs complete audit against the entire submission manifest.
        """
        errors = []
        checklist = manifest.get("checklist", {})
        license_meta = manifest.get("license", {})
        artifacts = manifest.get("artifacts", [])

        errors.extend(self.audit_checklist(checklist))
        errors.extend(self.audit_license_metadata(license_meta))
        errors.extend(self.audit_artifact_integrity(artifacts, virtual_fs=virtual_fs))

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }
