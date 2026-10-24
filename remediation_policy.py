from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class RemediationStrategy(str, Enum):
    PATCH = "PATCH"
    MITIGATE = "MITIGATE"
    ACCEPT_RISK = "ACCEPT_RISK"
    UPGRADE = "UPGRADE"


@dataclass(frozen=True)
class Vulnerability:
    cve_id: str
    severity: Severity
    cvss_score: float
    has_exploit_public: bool
    is_production_affecting: bool
    discovered_at: datetime


@dataclass(frozen=True)
class PolicyRule:
    name: str
    priority: int  # Lower number = higher priority
    severity: Optional[Severity]
    min_cvss: Optional[float]
    requires_public_exploit: Optional[bool]
    production_only: Optional[bool]
    sla_hours: int
    strategy: RemediationStrategy

    def matches(self, vuln: Vulnerability) -> bool:
        if self.severity is not None and vuln.severity != self.severity:
            return False
        if self.min_cvss is not None and vuln.cvss_score < self.min_cvss:
            return False
        if self.requires_public_exploit is not None and vuln.has_exploit_public != self.requires_public_exploit:
            return False
        if self.production_only is not None and vuln.is_production_affecting != self.production_only:
            return False
        return True


@dataclass(frozen=True)
class PolicyMatchResult:
    matched_rule: PolicyRule
    sla_deadline: datetime
    remediation_strategy: RemediationStrategy
    is_breached: bool


class RemediationPolicyMatrix:
    def __init__(self, rules: List[PolicyRule], default_sla_hours: int = 720):
        # Deterministic sorting: highest priority first (lowest priority int), then rule name alphabetically
        self.rules = sorted(rules, key=lambda r: (r.priority, r.name))
        self.default_sla_hours = default_sla_hours

    def evaluate(
        self, vuln: Vulnerability, evaluation_time: Optional[datetime] = None
    ) -> PolicyMatchResult:
        if evaluation_time is None:
            evaluation_time = vuln.discovered_at

        for rule in self.rules:
            if rule.matches(vuln):
                deadline = vuln.discovered_at + timedelta(hours=rule.sla_hours)
                is_breached = evaluation_time > deadline
                return PolicyMatchResult(
                    matched_rule=rule,
                    sla_deadline=deadline,
                    remediation_strategy=rule.strategy,
                    is_breached=is_breached,
                )

        fallback_rule = PolicyRule(
            name="DEFAULT_FALLBACK",
            priority=999999,
            severity=None,
            min_cvss=None,
            requires_public_exploit=None,
            production_only=None,
            sla_hours=self.default_sla_hours,
            strategy=RemediationStrategy.MITIGATE,
        )
        deadline = vuln.discovered_at + timedelta(hours=self.default_sla_hours)
        is_breached = evaluation_time > deadline
        return PolicyMatchResult(
            matched_rule=fallback_rule,
            sla_deadline=deadline,
            remediation_strategy=fallback_rule.strategy,
            is_breached=is_breached,
        )

    def assert_sla_threshold(
        self,
        vuln: Vulnerability,
        resolution_time: datetime,
        max_allowed_sla_hours: Optional[int] = None,
    ) -> None:
        result = self.evaluate(vuln, evaluation_time=resolution_time)
        actual_elapsed_hours = (resolution_time - vuln.discovered_at).total_seconds() / 3600.0

        if result.is_breached:
            raise AssertionError(
                f"SLA breached for {vuln.cve_id}: Elapsed {actual_elapsed_hours:.1f}h exceeds policy SLA of {result.matched_rule.sla_hours}h (Rule: {result.matched_rule.name})"
            )

        if max_allowed_sla_hours is not None and result.matched_rule.sla_hours > max_allowed_sla_hours:
            raise AssertionError(
                f"Policy SLA {result.matched_rule.sla_hours}h exceeds maximum acceptable threshold of {max_allowed_sla_hours}h"
            )
