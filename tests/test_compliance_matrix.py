import unittest
from compliance_matrix import (
    ComplianceMatrix,
    ComplianceStatus,
    ControlEvaluation,
    ControlRequirement,
    SLAPolicy,
    Standard,
)


class TestComplianceMatrixAndSLA(unittest.TestCase):

    def setUp(self):
        self.matrix = ComplianceMatrix()

        # Standard controls registration
        self.c1 = ControlRequirement(
            control_id="SOC2-CC1.1",
            name="Security Integrity",
            standard=Standard.SOC2,
            description="Commitment to integrity and ethical values",
            max_remediation_hours=24.0,
            severity="HIGH",
        )
        self.c2 = ControlRequirement(
            control_id="ISO-A.12.1",
            name="Operational Procedures",
            standard=Standard.ISO27001,
            description="Documented operating procedures",
            max_remediation_hours=48.0,
            severity="MEDIUM",
        )
        self.c3 = ControlRequirement(
            control_id="HIPAA-164.312",
            name="Encryption Standards",
            standard=Standard.HIPAA,
            description="Encryption at rest and transit",
            max_remediation_hours=4.0,
            severity="CRITICAL",
        )

        self.matrix.register_control(self.c1)
        self.matrix.register_control(self.c2)
        self.matrix.register_control(self.c3)

    def test_multi_standard_compliance_rate_calculation(self):
        self.matrix.record_evaluation(
            ControlEvaluation(control_id="SOC2-CC1.1", status=ComplianceStatus.COMPLIANT)
        )
        self.matrix.record_evaluation(
            ControlEvaluation(control_id="ISO-A.12.1", status=ComplianceStatus.COMPLIANT)
        )
        self.matrix.record_evaluation(
            ControlEvaluation(control_id="HIPAA-164.312", status=ComplianceStatus.NON_COMPLIANT)
        )

        # Overall rate: 2/3 compliant (~0.6667)
        overall_rate = self.matrix.calculate_compliance_rate()
        self.assertAlmostEqual(overall_rate, 2.0 / 3.0, places=4)

        # Filter by standard
        soc2_rate = self.matrix.calculate_compliance_rate(Standard.SOC2)
        hipaa_rate = self.matrix.calculate_compliance_rate(Standard.HIPAA)
        self.assertEqual(soc2_rate, 1.0)
        self.assertEqual(hipaa_rate, 0.0)

    def test_sla_policy_assertions_pass(self):
        # Record compliant status and remediation within SLA thresholds
        self.matrix.record_evaluation(
            ControlEvaluation(control_id="SOC2-CC1.1", status=ComplianceStatus.COMPLIANT, remediation_time_hours=12.0)
        )
        self.matrix.record_evaluation(
            ControlEvaluation(control_id="ISO-A.12.1", status=ComplianceStatus.COMPLIANT, remediation_time_hours=10.0)
        )
        self.matrix.record_evaluation(
            ControlEvaluation(control_id="HIPAA-164.312", status=ComplianceStatus.COMPLIANT, remediation_time_hours=2.0)
        )

        policy = SLAPolicy(
            policy_id="SLA-DEFAULT",
            name="Standard SLA",
            max_allowed_high_severity_hours=24.0,
            max_allowed_critical_severity_hours=4.0,
            required_overall_compliance_rate=1.0,
        )

        sla_result = self.matrix.verify_sla(policy)
        self.assertTrue(sla_result["overall_sla_met"])
        self.assertTrue(sla_result["rate_sla_met"])
        self.assertTrue(sla_result["critical_sla_met"])
        self.assertTrue(sla_result["high_sla_met"])

    def test_sla_policy_assertions_fail_on_breach(self):
        # Breaches critical SLA remediation time (6.0 > 4.0 limit)
        self.matrix.record_evaluation(
            ControlEvaluation(control_id="SOC2-CC1.1", status=ComplianceStatus.COMPLIANT, remediation_time_hours=5.0)
        )
        self.matrix.record_evaluation(
            ControlEvaluation(control_id="HIPAA-164.312", status=ComplianceStatus.COMPLIANT, remediation_time_hours=6.0)
        )

        policy = SLAPolicy(
            policy_id="SLA-STRICT",
            name="Strict SLA",
            max_allowed_high_severity_hours=12.0,
            max_allowed_critical_severity_hours=4.0,
            required_overall_compliance_rate=0.8,
        )

        sla_result = self.matrix.verify_sla(policy)
        self.assertFalse(sla_result["overall_sla_met"])
        self.assertFalse(sla_result["critical_sla_met"])
        self.assertTrue(sla_result["high_sla_met"])
        self.assertTrue(sla_result["rate_sla_met"])

    def test_unregistered_control_evaluation_raises_error(self):
        invalid_eval = ControlEvaluation(control_id="UNKNOWN-01", status=ComplianceStatus.COMPLIANT)
        with self.assertRaises(ValueError):
            self.matrix.record_evaluation(invalid_eval)


if __name__ == "__main__":
    unittest.main()
