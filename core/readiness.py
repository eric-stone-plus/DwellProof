"""Due-diligence readiness gate for directional investment advice.

Passing this gate only means the minimum evidence set is present and verified;
it is not a legal opinion, valuation, or recommendation by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Mapping

from .contracts import (
    CategoricalEvidence,
    ContractError,
    EvidenceKind,
    EvidenceNotUsableError,
    EvidenceReference,
    EvidenceRole,
    EvidenceStatus,
    category_evidence_reference,
    require_verified_category,
)


class CheckName(str, Enum):
    TITLE = "title"
    ENCUMBRANCE = "mortgage_seizure_encumbrance"
    PROPERTY_NATURE = "property_nature"
    TENANCY = "tenancy"
    TAX = "tax"
    LOAN = "loan"
    COMPARABLE_SALES = "comparable_sales"


class CheckOutcome(str, Enum):
    CLEAR = "clear"
    ADVERSE = "adverse"
    UNKNOWN = "unknown"


CHECK_ROLES = {
    CheckName.TITLE: EvidenceRole.TITLE_CHECK,
    CheckName.ENCUMBRANCE: EvidenceRole.ENCUMBRANCE_CHECK,
    CheckName.PROPERTY_NATURE: EvidenceRole.PROPERTY_NATURE_CHECK,
    CheckName.TENANCY: EvidenceRole.TENANCY_CHECK,
    CheckName.TAX: EvidenceRole.TAX_CHECK,
    CheckName.LOAN: EvidenceRole.LOAN_CHECK,
    CheckName.COMPARABLE_SALES: EvidenceRole.COMPARABLE_SALES_CHECK,
}


@dataclass(frozen=True)
class ReadinessResult:
    analysis_ready: bool
    decision: str
    evaluated_as_of: date
    blockers: tuple[str, ...]
    passed_checks: tuple[CheckName, ...]
    evidence_ids: tuple[str, ...]
    input_evidence: tuple[EvidenceReference, ...]

    def __post_init__(self) -> None:
        if type(self.evaluated_as_of) is not date:
            raise ContractError("readiness evaluated_as_of must be a date")
        expected_ready = (
            self.analysis_ready
            and self.decision == "ANALYSIS_READY"
            and not self.blockers
        )
        expected_closed = (
            not self.analysis_ready
            and self.decision == "INSUFFICIENT_EVIDENCE"
            and bool(self.blockers)
        )
        if not (expected_ready or expected_closed):
            raise ContractError("readiness state fields are inconsistent")
        reference_ids = tuple(item.evidence_id for item in self.input_evidence)
        if reference_ids != self.evidence_ids:
            raise ContractError("readiness evidence IDs must match references")
        if len(self.passed_checks) != len(set(self.passed_checks)):
            raise ContractError("readiness passed checks must be unique")

        scopes = {
            (item.case_id, item.property_id, item.borrower_id)
            for item in self.input_evidence
        }
        for item in self.input_evidence:
            if (
                item.kind is not EvidenceKind.DUE_DILIGENCE_CHECK
                or item.status is not EvidenceStatus.VERIFIED
                or item.value != CheckOutcome.CLEAR.value
                or not item.valid_from <= self.evaluated_as_of <= item.valid_until
                or max(
                    item.observation_end,
                    item.published_at.date(),
                    item.retrieved_at.date(),
                )
                > self.evaluated_as_of
            ):
                if self.analysis_ready:
                    raise ContractError("open readiness contains unusable evidence")

        if self.analysis_ready and (
            set(self.passed_checks) != set(REQUIRED_CHECKS)
            or len(self.input_evidence) != len(REQUIRED_CHECKS)
            or len(self.evidence_ids) != len(set(self.evidence_ids))
            or len(scopes) != 1
            or any(not item.borrower_id for item in self.input_evidence)
            or self.passed_checks != REQUIRED_CHECKS
            or any(
                item.name != check.value
                or item.role is not CHECK_ROLES[check]
                for check, item in zip(REQUIRED_CHECKS, self.input_evidence)
            )
        ):
            raise ContractError("open readiness requires all seven checks")


REQUIRED_CHECKS = tuple(CheckName)


def evaluate_buy_readiness(
    checks: Mapping[CheckName, CategoricalEvidence[CheckOutcome]],
    *,
    as_of: date,
) -> ReadinessResult:
    """Fail closed unless every required check is verified and explicitly clear."""

    if not isinstance(checks, Mapping):
        raise ContractError("checks must be a mapping")
    if type(as_of) is not date:
        raise ContractError("as_of must be a date")
    blockers: list[str] = []
    evidence_ids: list[str] = []
    passed_checks: list[CheckName] = []
    input_evidence: list[EvidenceReference] = []
    for name in REQUIRED_CHECKS:
        evidence = checks.get(name)
        if evidence is None:
            blockers.append(f"{name.value}:missing")
            continue
        if not isinstance(evidence, CategoricalEvidence):
            blockers.append(f"{name.value}:invalid_evidence")
            continue
        evidence_ids.append(evidence.metadata.evidence_id)
        input_evidence.append(category_evidence_reference(evidence))
        if evidence.name != name.value:
            blockers.append(f"{name.value}:wrong_check_name")
            continue
        try:
            outcome = require_verified_category(
                evidence,
                as_of=as_of,
                expected_kind=EvidenceKind.DUE_DILIGENCE_CHECK,
                expected_role=CHECK_ROLES[name],
            )
        except EvidenceNotUsableError as exc:
            blockers.append(f"{name.value}:not_usable:{exc}")
            continue
        if not isinstance(outcome, CheckOutcome):
            blockers.append(f"{name.value}:invalid_outcome")
        elif outcome is not CheckOutcome.CLEAR:
            blockers.append(f"{name.value}:{outcome.value}")
        else:
            passed_checks.append(name)

    if len(evidence_ids) != len(set(evidence_ids)):
        blockers.append("evidence_id:duplicate")
    scopes = {
        (item.case_id, item.property_id, item.borrower_id)
        for item in input_evidence
    }
    if len(scopes) > 1:
        blockers.append("evidence_scope:mismatch")
    if any(not item.borrower_id for item in input_evidence):
        blockers.append("borrower_id:missing")

    ready = not blockers
    return ReadinessResult(
        analysis_ready=ready,
        decision="ANALYSIS_READY" if ready else "INSUFFICIENT_EVIDENCE",
        evaluated_as_of=as_of,
        blockers=tuple(blockers),
        passed_checks=tuple(passed_checks),
        evidence_ids=tuple(evidence_ids),
        input_evidence=tuple(input_evidence),
    )


def guarded_decision(
    requested_decision: str,
    readiness: ReadinessResult,
) -> str:
    """Never turn readiness alone into a directional recommendation.

    The requested label is accepted for compatibility with the legacy caller,
    but an open gate returns only ``ANALYSIS_READY``.  A separate deterministic
    recommendation policy must be implemented and tested before BUY/SELL/HOLD
    may be emitted.
    """

    if not isinstance(readiness, ReadinessResult):
        return "INSUFFICIENT_EVIDENCE"
    if not isinstance(requested_decision, str) or not requested_decision.strip():
        return "INSUFFICIENT_EVIDENCE"
    if not readiness.analysis_ready:
        return "INSUFFICIENT_EVIDENCE"
    return "ANALYSIS_READY"
