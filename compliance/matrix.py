import enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set


class Standard(enum.Enum):
    SOC2 = "SOC2"
    ISO27001 = "ISO27001"
    HIPAA = "HIPAA"
    GDPR = "GDPR"
    PCI_DSS = "PCI_DSS"


class Severity(enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ComplianceStatus(enum.Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


@dataclass(frozen=True)
class SLAPolicy:
    max_resolution_hours: float
    uptime_target_percent: float
    breach_penalty_usd: float = 0.0

    def is_resolution_met(self, actual_resolution_hours: float) -> bool:
        return actual_resolution_hours <= self.max_resolution_hours

    def is_uptime_met(self, actual_uptime_percent: float) -> bool:
        return actual_uptime_percent >= self.uptime_target_percent


@dataclass(frozen=True)
class ComplianceControl:
    control_id: str
    name: str
    standards: Set[Standard]
    severity: Severity
    sla_policy: SLAPolicy


@dataclass
class EvaluationResult:
    control_id: str
    status: ComplianceStatus
    sla_breached: bool
    details: str


class ComplianceMatrix:
    def __init__(self) -> None:
        self._controls: Dict[str, ComplianceControl] = {}

    def register_control(self, control: ComplianceControl) -> None:
        if control.control_id in self._controls:
            raise ValueError(f"Control {control.control_id} already registered")
        self._controls[control.control_id] = control

    def get_control(self, control_id: str) -> Optional[ComplianceControl]:
        return self._controls.get(control_id)

    def get_controls_for_standard(self, standard: Standard) -> List[ComplianceControl]:
        # Deterministic sorting by control_id
        matched = [ctrl for ctrl in self._controls.values() if standard in ctrl.standards]
        return sorted(matched, key=lambda c: c.control_id)

    def evaluate_control(
        self,
        control_id: str,
        is_passing: bool,
        actual_resolution_hours: float,
        actual_uptime_percent: float,
    ) -> EvaluationResult:
        control = self._controls.get(control_id)
        if not control:
            raise KeyError(f"Control {control_id} not found in matrix")

        sla = control.sla_policy
        res_met = sla.is_resolution_met(actual_resolution_hours)
        uptime_met = sla.is_uptime_met(actual_uptime_percent)
        sla_breached = not (res_met and uptime_met)

        if not is_passing:
            status = ComplianceStatus.NON_COMPLIANT
            details = "Control check failed"
        elif sla_breached:
            status = ComplianceStatus.NON_COMPLIANT
            reasons = []
            if not res_met:
                reasons.append(f"Resolution SLA breached: {actual_resolution_hours}h > {sla.max_resolution_hours}h")
            if not uptime_met:
                reasons.append(f"Uptime SLA breached: {actual_uptime_percent}% < {sla.uptime_target_percent}%")
            details = "; ".join(reasons)
        else:
            status = ComplianceStatus.COMPLIANT
            details = "All checks and SLAs satisfied"

        return EvaluationResult(
            control_id=control_id,
            status=status,
            sla_breached=sla_breached,
            details=details,
        )

    def evaluate_standard_compliance(
        self,
        standard: Standard,
        metrics_by_control: Dict[str, Dict[str, float]],
    ) -> Dict[str, EvaluationResult]:
        """
        Evaluates all controls associated with a standard in deterministic order.
        """
        controls = self.get_controls_for_standard(standard)
        results: Dict[str, EvaluationResult] = {}
        for ctrl in controls:
            m = metrics_by_control.get(ctrl.control_id, {})
            is_passing = bool(m.get("is_passing", True))
            res_hours = float(m.get("actual_resolution_hours", 0.0))
            uptime_pct = float(m.get("actual_uptime_percent", 100.0))
            results[ctrl.control_id] = self.evaluate_control(
                control_id=ctrl.control_id,
                is_passing=is_passing,
                actual_resolution_hours=res_hours,
                actual_uptime_percent=uptime_pct,
            )
        return results
