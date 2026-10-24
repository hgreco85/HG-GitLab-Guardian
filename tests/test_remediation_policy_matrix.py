from datetime import datetime, timedelta
import unittest

from remediation_policy import (
    PolicyRule,
    RemediationPolicyMatrix,
    RemediationStrategy,
    Severity,
    Vulnerability,
)


class TestRemediationPolicyMatrix(unittest.TestCase):
    def setUp(self):
        self.base_time = datetime(2026, 1, 1, 12, 0, 0)
        self.rules = [
            PolicyRule(
                name="Critical Active Exploit in Prod",
                priority=10,
                severity=Severity.CRITICAL,
                min_cvss=9.0,
                requires_public_exploit=True,
                production_only=True,
                sla_hours=24,
                strategy=RemediationStrategy.PATCH,
            ),
            PolicyRule(
                name="Critical Standard Prod",
                priority=20,
                severity=Severity.CRITICAL,
                min_cvss=9.0,
                requires_public_exploit=None,
                production_only=True,
                sla_hours=48,
                strategy=RemediationStrategy.PATCH,
            ),
            PolicyRule(
                name="High Severity Prod",
                priority=30,
                severity=Severity.HIGH,
                min_cvss=7.0,
                requires_public_exploit=None,
                production_only=True,
                sla_hours=168,  # 7 days
                strategy=RemediationStrategy.UPGRADE,
            ),
            PolicyRule(
                name="Medium General",
                priority=40,
                severity=Severity.MEDIUM,
                min_cvss=4.0,
                requires_public_exploit=None,
                production_only=None,
                sla_hours=336,  # 14 days
                strategy=RemediationStrategy.MITIGATE,
            ),
        ]
        self.matrix = RemediationPolicyMatrix(self.rules, default_sla_hours=720)

    def test_deterministic_priority_matching(self):
        # Matches both 'Critical Active Exploit in Prod' and 'Critical Standard Prod'
        # Highest priority (lowest number: 10) must deterministically win
        vuln = Vulnerability(
            cve_id="CVE-2026-1001",
            severity=Severity.CRITICAL,
            cvss_score=9.8,
            has_exploit_public=True,
            is_production_affecting=True,
            discovered_at=self.base_time,
        )

        result = self.matrix.evaluate(vuln)
        self.assertEqual(result.matched_rule.name, "Critical Active Exploit in Prod")
        self.assertEqual(result.matched_rule.sla_hours, 24)
        self.assertEqual(result.remediation_strategy, RemediationStrategy.PATCH)
        self.assertEqual(result.sla_deadline, self.base_time + timedelta(hours=24))
        self.assertFalse(result.is_breached)

    def test_fallback_when_no_rule_matches(self):
        vuln = Vulnerability(
            cve_id="CVE-2026-9999",
            severity=Severity.INFO,
            cvss_score=1.0,
            has_exploit_public=False,
            is_production_affecting=False,
            discovered_at=self.base_time,
        )

        result = self.matrix.evaluate(vuln)
        self.assertEqual(result.matched_rule.name, "DEFAULT_FALLBACK")
        self.assertEqual(result.matched_rule.sla_hours, 720)
        self.assertEqual(result.remediation_strategy, RemediationStrategy.MITIGATE)
        self.assertEqual(result.sla_deadline, self.base_time + timedelta(hours=720))
        self.assertFalse(result.is_breached)

    def test_sla_threshold_assertions_passed_and_breached(self):
        vuln = Vulnerability(
            cve_id="CVE-2026-2002",
            severity=Severity.HIGH,
            cvss_score=8.5,
            has_exploit_public=False,
            is_production_affecting=True,
            discovered_at=self.base_time,
        )

        # SLA is 168 hours
        resolved_on_time = self.base_time + timedelta(hours=100)
        # Should not raise
        self.matrix.assert_sla_threshold(vuln, resolved_on_time, max_allowed_sla_hours=200)

        # Resolving past SLA deadline raises AssertionError
        resolved_late = self.base_time + timedelta(hours=170)
        with self.assertRaises(AssertionError) as ctx:
            self.matrix.assert_sla_threshold(vuln, resolved_late)
        self.assertIn("SLA breached", str(ctx.exception))

        # Test max allowed SLA threshold assertion
        with self.assertRaises(AssertionError) as ctx2:
            self.matrix.assert_sla_threshold(vuln, resolved_on_time, max_allowed_sla_hours=72)
        self.assertIn("exceeds maximum acceptable threshold", str(ctx2.exception))


if __name__ == "__main__":
    unittest.main()
