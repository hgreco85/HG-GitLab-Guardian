import hashlib
import os
import re

REQUIRED_CHECKLIST_ITEMS = [
    "README.md",
    "LICENSE",
    "metadata.json",
    "src/",
    "tests/",
]

VALID_LICENSES = {
    "MIT": "MIT License",
    "Apache-2.0": "Apache License, Version 2.0",
    "BSD-3-Clause": "BSD 3-Clause \"New\" or \"Revised\" License",
    "GPL-3.0": "GNU General Public License v3.0",
}


def calculate_file_hash(filepath: str, algorithm: str = "sha256") -> str:
    """Calculate deterministic hash of a file."""
    hasher = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def audit_checklist(manifest_paths: list[str]) -> tuple[bool, list[str]]:
    """Validates that all required package checklist items are covered by the manifest paths."""
    normalized_paths = [p.replace("\\", "/").lstrip("/") for p in manifest_paths]
    missing = []
    for req in REQUIRED_CHECKLIST_ITEMS:
        if req.endswith("/"):
            prefix = req.rstrip("/")
            if not any(p == prefix or p.startswith(prefix + "/") for p in normalized_paths):
                missing.append(req)
        else:
            if req not in normalized_paths:
                missing.append(req)
    return (len(missing) == 0, missing)


def audit_license_metadata(license_name: str, license_content: str | None = None) -> tuple[bool, str]:
    """Audits that the license is approved and optionally matches canonical signature patterns."""
    if not license_name or license_name not in VALID_LICENSES:
        return False, f"Invalid or unrecognized license identifier: '{license_name}'. Allowed: {sorted(list(VALID_LICENSES.keys()))}"
    
    if license_content is not None:
        expected_phrase = VALID_LICENSES[license_name]
        if expected_phrase.lower() not in license_content.lower() and license_name.lower() not in license_content.lower():
            return False, f"License file content does not match expected identifier/text for '{license_name}'"
            
    return True, "License metadata is valid"


def audit_artifact_integrity(manifest_checksums: dict[str, str], base_dir: str = ".", algorithm: str = "sha256") -> tuple[bool, list[str]]:
    """Audits deterministic artifact integrity against manifest checksums."""
    mismatches = []
    for rel_path, expected_hash in manifest_checksums.items():
        full_path = os.path.join(base_dir, rel_path)
        if not os.path.exists(full_path):
            mismatches.append(f"Missing file: {rel_path}")
            continue
        actual_hash = calculate_file_hash(full_path, algorithm=algorithm)
        if actual_hash.lower() != expected_hash.lower():
            mismatches.append(
                f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"
            )
    return (len(mismatches) == 0, mismatches)
