import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


class Standard(enum.Enum):
    SOC2 = "SOC2"
    ISO27001 = "ISO27001"
    HIPAA = "HIPAA"
    GDPR = "GDPR"
    PCI_DSS = "PCI_DSS"


class ComplianceStatus(enum.Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class ControlRequirement:
    control_id: str
    name: str
    standard: Standard
    description: str
    max_remediation_hours: float
    severity: str = "MEDIUM"  # LOW, MEDIUM, HIGH, CRITICAL


@dataclass
class ControlEvaluation:
    control_id: str
    status: ComplianceStatus
    remediation_time_hours: float = 0.0
    notes: str = ""


@dataclass
class SLAPolicy:
    policy_id: str
    name: str
    max_allowed_high_severity_hours: float
    max_allowed_critical_severity_hours: float
    required_overall_compliance_rate: float  # Value between 0.0 and 1.0


class ComplianceMatrix:
    """Deterministic multi-standard compliance matrix with SLA enforcement."""

    def __init__(self) -> None:
        self._controls: Dict[str, ControlRequirement] = {}
        self._evaluations: Dict[str, ControlEvaluation] = {}

    def register_control(self, requirement: ControlRequirement) -> None:
        self._controls[requirement.control_id] = requirement

    def record_evaluation(self, evaluation: ControlEvaluation) -> None:
        if evaluation.control_id not in self._controls:
            raise ValueError(f"Control {evaluation.control_id} is not registered in matrix.")
        self._evaluations[evaluation.control_id] = evaluation

    def get_standard_controls(self, standard: Standard) -> List[ControlRequirement]:
        return sorted(
            [ctrl for ctrl in self._controls.values() if ctrl.standard == standard],
            key=lambda c: c.control_id,
        )

    def calculate_compliance_rate(self, standard: Optional[Standard] = None) -> float:
        target_controls = (
            self.get_standard_controls(standard)
            if standard
            else sorted(self._controls.values(), key=lambda c: c.control_id)
        )
        applicable = [
            c for c in target_controls
            if c.control_id in self._evaluations
            and self._evaluations[c.control_id].status != ComplianceStatus.NOT_APPLICABLE
        ]
        if not applicable:
            return 1.0

        compliant_count = sum(
            1 for c in applicable
            if self._evaluations[c.control_id].status == ComplianceStatus.COMPLIANT
        )
        return compliant_count / len(applicable)

    def verify_sla(self, policy: SLAPolicy) -> Dict[str, bool]:
        """Asserts compliance against SLA policy constraints deterministically."""
        compliance_rate = self.calculate_compliance_rate()
        rate_met = compliance_rate >= policy.required_overall_compliance_rate

        critical_sla_met = True
        high_sla_met = True

        for ctrl_id, eval_item in self._evaluations.items():
            ctrl = self._controls[ctrl_id]
            if ctrl.severity == "CRITICAL" and eval_item.remediation_time_hours > policy.max_allowed_critical_severity_hours:
                critical_sla_met = False
            if ctrl.severity == "HIGH" and eval_item.remediation_time_hours > policy.max_allowed_high_severity_hours:
                high_sla_met = False

        overall = rate_met and critical_sla_met and high_sla_met
        return {
            "overall_sla_met": overall,
            "rate_sla_met": rate_met,
            "critical_sla_met": critical_sla_met,
            "high_sla_met": high_sla_met,
        }
