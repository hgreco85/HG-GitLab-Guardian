"""GitLab CI/CD Pipeline triage engine: analyzes failure logs and categorizes incidents."""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from security_guard import sanitize_text

# Regex patterns for diagnosing common CI/CD failures
ASSERTION_PATTERN = re.compile(r"AssertionError:\s*(.+)", re.MULTILINE)
IMPORT_ERROR_PATTERN = re.compile(r"ModuleNotFoundError:\s*No module named ['\"]([^'\"]+)['\"]", re.MULTILINE)
SECURITY_CVE_PATTERN = re.compile(r"(CVE-\d{4}-\d+|GHSA-[a-z0-9-]+)", re.IGNORECASE)
TIMEOUT_PATTERN = re.compile(r"(timed? out|deadline exceeded)", re.IGNORECASE)
SECRET_LEAK_PATTERN = re.compile(r"(private_key|api_key|token|password|credential) detected in log", re.IGNORECASE)


class TriageDiagnosis:
    def __init__(
        self,
        category: str,
        root_cause: str,
        failing_component: str,
        confidence: float,
        proposed_action: str,
        evidence_snippet: str,
    ):
        self.category = category
        self.root_cause = root_cause
        self.failing_component = failing_component
        self.confidence = confidence
        self.proposed_action = proposed_action
        self.evidence_snippet = evidence_snippet

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category,
            "root_cause": self.root_cause,
            "failing_component": self.failing_component,
            "confidence": self.confidence,
            "proposed_action": self.proposed_action,
            "evidence_snippet": self.evidence_snippet,
        }


def analyze_pipeline_log(log_text: str, event_summary: str = "") -> TriageDiagnosis:
    """Performs deterministic causal analysis on failing job logs."""
    from security_guard import scan_for_secrets
    
    # 1. Secret leakage in build / test log or summary
    has_raw_secret, secret_reason = scan_for_secrets(log_text + " " + event_summary)
    if has_raw_secret or SECRET_LEAK_PATTERN.search(log_text):
        return TriageDiagnosis(
            category="SECRET_LEAKAGE",
            root_cause="Job output or event contains leaked credentials",
            failing_component="ci_job_output_sanitizer",
            confidence=0.99,
            proposed_action="Immediately purge contaminated build artifacts, rotate token, and enable masking",
            evidence_snippet=secret_reason or "Sensitive credential detected",
        )

    clean_log = sanitize_text(log_text)

    # 2. Dependency security advisory / CVE
    cve_match = SECURITY_CVE_PATTERN.search(clean_log)
    if cve_match or "security_alert" in event_summary:
        cve_id = cve_match.group(1) if cve_match else "CVE-KNOWN-VULN"
        return TriageDiagnosis(
            category="SECURITY_ADVISORY",
            root_cause=f"High/Critical security advisory detected in dependencies: {cve_id}",
            failing_component="dependency_lockfile",
            confidence=0.95,
            proposed_action=f"Update patched dependency version for {cve_id} and regenerate lockfile",
            evidence_snippet=cve_id,
        )

    # 3. Test assertion failure
    assert_match = ASSERTION_PATTERN.search(clean_log)
    if assert_match or "test_failed" in event_summary or "unit-test job failed" in event_summary:
        detail = assert_match.group(1) if assert_match else "Assertion mismatch after code modification"
        return TriageDiagnosis(
            category="TEST_REGRESSION",
            root_cause=f"Unit test regression: {detail}",
            failing_component="test_suite",
            confidence=0.92,
            proposed_action="Generate minimal reproducible regression test case and propose fix patch",
            evidence_snippet=detail,
        )

    # 4. Import / Missing module error
    import_match = IMPORT_ERROR_PATTERN.search(clean_log)
    if import_match:
        mod_name = import_match.group(1)
        return TriageDiagnosis(
            category="DEPENDENCY_MISSING",
            root_cause=f"Module '{mod_name}' is required by test runner but not declared in requirements",
            failing_component="pyproject.toml/requirements.txt",
            confidence=0.94,
            proposed_action=f"Add '{mod_name}' to pyproject.toml / requirements.txt",
            evidence_snippet=f"Missing module: {mod_name}",
        )

    # 5. Default generic CI failure
    return TriageDiagnosis(
        category="PIPELINE_FAILURE",
        root_cause="General pipeline job failed with non-zero exit code",
        failing_component="gitlab_ci_runner",
        confidence=0.75,
        proposed_action="Inspect runner environment, dependencies, and gitlab-ci.yml configuration",
        evidence_snippet=clean_log[:150],
    )
