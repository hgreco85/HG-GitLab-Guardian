import hashlib
import json
from typing import Dict, Any, List, Optional, Tuple


class SBOMVerificationError(Exception):
    """Base exception raised for SBOM verification failures."""
    pass


class IntegrityMismatchError(SBOMVerificationError):
    """Raised when package content does not match expected SHA-256 hash."""
    pass


class ProvenanceError(SBOMVerificationError):
    """Raised when package provenance/metadata is invalid or tampered."""
    pass


class SBOMProvenanceVerifier:
    """
    Deterministic supply chain SBOM package integrity and SHA-256 provenance verifier.
    """

    def __init__(self, expected_author: Optional[str] = None, allowed_licenses: Optional[List[str]] = None):
        self.expected_author = expected_author
        self.allowed_licenses = allowed_licenses

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """Compute deterministic lowercase hexadecimal SHA-256 digest."""
        return hashlib.sha256(data).hexdigest()

    def verify_package_bytes(self, package_bytes: bytes, expected_sha256: str) -> bool:
        """
        Verify integrity of raw package bytes against expected SHA-256 hash.
        Raises IntegrityMismatchError if hashes do not match.
        """
        actual_sha256 = self.compute_sha256(package_bytes)
        if actual_sha256.lower() != expected_sha256.lower():
            raise IntegrityMismatchError(
                f"Hash mismatch! Expected {expected_sha256.lower()}, got {actual_sha256.lower()}"
            )
        return True

    def verify_component(self, component: Dict[str, Any], component_data: Optional[bytes] = None) -> Tuple[bool, str]:
        """
        Verify a single SBOM component dictionary for metadata provenance and payload integrity.
        """
        name = component.get("name")
        version = component.get("version")
        hashes = component.get("hashes", {})

        if not name or not version:
            raise ProvenanceError("Component must specify 'name' and 'version'")

        expected_sha256 = hashes.get("SHA-256") or hashes.get("sha256")
        if not expected_sha256:
            raise ProvenanceError(f"Component '{name}' missing SHA-256 checksum in hashes")

        if self.allowed_licenses is not None:
            comp_license = component.get("license")
            if comp_license not in self.allowed_licenses:
                raise ProvenanceError(
                    f"Component '{name}' license '{comp_license}' is not in allowed licenses: {self.allowed_licenses}"
                )

        if component_data is not None:
            self.verify_package_bytes(component_data, expected_sha256)

        return True, f"Component '{name}@{version}' successfully verified."

    def verify_sbom(self, sbom_manifest: Dict[str, Any], package_artifacts: Optional[Dict[str, bytes]] = None) -> Dict[str, Any]:
        """
        Verify an entire SBOM document including root metadata and components.
        """
        package_artifacts = package_artifacts or {}

        if sbom_manifest.get("bomFormat") != "CycloneDX" and "spdxVersion" not in sbom_manifest:
            # General minimal schema check
            if "components" not in sbom_manifest and "packages" not in sbom_manifest:
                raise ProvenanceError("Invalid SBOM format: missing 'components' or 'packages' list.")

        metadata = sbom_manifest.get("metadata", {})
        if self.expected_author:
            authors = metadata.get("authors", [])
            author_names = [a.get("name") if isinstance(a, dict) else str(a) for a in authors]
            if self.expected_author not in author_names:
                raise ProvenanceError(f"Author '{self.expected_author}' not found in SBOM metadata authors.")

        components = sbom_manifest.get("components", [])
        verified_components = []

        for comp in components:
            comp_name = comp.get("name")
            data = package_artifacts.get(comp_name)
            self.verify_component(comp, component_data=data)
            verified_components.append(comp_name)

        return {
            "status": "VERIFIED",
            "verified_components": verified_components,
            "total_verified": len(verified_components)
        }
