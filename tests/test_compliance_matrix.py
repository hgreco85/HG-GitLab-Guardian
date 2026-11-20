import unittest
from compliance.matrix import (
    Standard,
    Severity,
    ComplianceStatus,
    SLAPolicy,
    ComplianceControl,
    ComplianceMatrix,
)


class TestComplianceMatrix(unittest.TestCase):
    def setUp(self) -> None:
        self.matrix = ComplianceMatrix()

        self.ctrl_access = ComplianceControl(
            control_id="AC-01",
            name="Access Control and Revocation",
            standards={Standard.SOC2, Standard.ISO27001, Standard.HIPAA},
            severity=Severity.HIGH,
            sla_policy=SLAPolicy(
                max_resolution_hours=4.0,
                uptime_target_percent=99.9,
                breach_penalty_usd=500.0,
            ),
        )

        self.ctrl_encryption = ComplianceControl(
            control_id="CR-02",
            name="Data-at-Rest Encryption",
            standards={Standard.SOC2, Standard.PCI_DSS, Standard.GDPR},
            severity=Severity.CRITICAL,
            sla_policy=SLAPolicy(
                max_resolution_hours=1.0,
                uptime_target_percent=99.99,
                breach_penalty_usd=2500.0,
            ),
        )

        self.ctrl_logging = ComplianceControl(
            control_id="AU-03",
            name="Audit Log Retention",
            standards={Standard.ISO27001, Standard.HIPAA, Standard.GDPR},
            severity=Severity.MEDIUM,
            sla_policy=SLAPolicy(
                max_resolution_hours=24.0,
                uptime_target_percent=99.0,
                breach_penalty_usd=100.0,
            ),
        )

        self.matrix.register_control(self.ctrl_access)
        self.matrix.register_control(self.ctrl_encryption)
        self.matrix.register_control(self.ctrl_logging)

    def test_multi_standard_mapping_and_deterministic_ordering(self) -> None:
        # Ensure controls mapped to Standard.SOC2 are returned in sorted order by control_id
        soc2_controls = self.matrix.get_controls_for_standard(Standard.SOC2)
        soc2_ids = [c.control_id for c in soc2_controls]
        self.assertEqual(soc2_ids, ["AC-01", "CR-02"])

        # Standard.HIPAA
        hipaa_controls = self.matrix.get_controls_for_standard(Standard.HIPAA)
        hipaa_ids = [c.control_id for c in hipaa_controls]
        self.assertEqual(hipaa_ids, ["AC-01", "AU-03"])

        # Standard.GDPR
        gdpr_controls = self.matrix.get_controls_for_standard(Standard.GDPR)
        gdpr_ids = [c.control_id for c in gdpr_controls]
        self.assertEqual(gdpr_ids, ["AU-03", "CR-02"])

        # Duplicate registration raises ValueError
        with self.assertRaises(ValueError):
            self.matrix.register_control(self.ctrl_access)

    def test_sla_policy_assertions_within_thresholds(self) -> None:
        # Passing control check with metrics strictly within SLA limits
        res = self.matrix.evaluate_control(
            control_id="AC-01",
            is_passing=True,
            actual_resolution_hours=2.5,  # target <= 4.0
            actual_uptime_percent=99.95,   # target >= 99.9
        )
        self.assertEqual(res.status, ComplianceStatus.COMPLIANT)
        self.assertFalse(res.sla_breached)
        self.assertIn("satisfied", res.details)

    def test_sla_policy_breach_detection_and_non_compliance(self) -> None:
        # Control check passes functionally, but breaches resolution time SLA
        res_res_breached = self.matrix.evaluate_control(
            control_id="CR-02",
            is_passing=True,
            actual_resolution_hours=2.0,  # exceeds target of 1.0
            actual_uptime_percent=99.99,
        )
        self.assertEqual(res_res_breached.status, ComplianceStatus.NON_COMPLIANT)
        self.assertTrue(res_res_breached.sla_breached)
        self.assertIn("Resolution SLA breached", res_res_breached.details)

        # Breaches uptime target
        res_uptime_breached = self.matrix.evaluate_control(
            control_id="CR-02",
            is_passing=True,
            actual_resolution_hours=0.5,
            actual_uptime_percent=99.90,  # below target of 99.99
        )
        self.assertEqual(res_uptime_breached.status, ComplianceStatus.NON_COMPLIANT)
        self.assertTrue(res_uptime_breached.sla_breached)
        self.assertIn("Uptime SLA breached", res_uptime_breached.details)

    def test_standard_level_batch_evaluation_determinism(self) -> None:
        metrics = {
            "AC-01": {"is_passing": True, "actual_resolution_hours": 1.0, "actual_uptime_percent": 99.95},
            "CR-02": {"is_passing": True, "actual_resolution_hours": 5.0, "actual_uptime_percent": 99.99},
        }
        evaluations = self.matrix.evaluate_standard_compliance(Standard.SOC2, metrics)
        self.assertEqual(list(evaluations.keys()), ["AC-01", "CR-02"])
        self.assertEqual(evaluations["AC-01"].status, ComplianceStatus.COMPLIANT)
        self.assertEqual(evaluations["CR-02"].status, ComplianceStatus.NON_COMPLIANT)
        self.assertTrue(evaluations["CR-02"].sla_breached)


if __name__ == "__main__":
    unittest.main()
