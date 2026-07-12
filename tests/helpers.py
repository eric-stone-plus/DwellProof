from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import TypeVar

from core.contracts import (
    CategoricalEvidence,
    EvidenceKind,
    EvidenceMetadata,
    EvidenceRole,
    EvidenceStatus,
    NumericEvidence,
    ObservationPeriod,
    Unit,
)


T = TypeVar("T")


def metadata(
    evidence_id: str,
    status: EvidenceStatus = EvidenceStatus.VERIFIED,
    kind: EvidenceKind = EvidenceKind.TRANSACTION_INPUT,
    role: EvidenceRole = EvidenceRole.PURCHASE_PRICE,
    evidence_date: date = date(2026, 7, 1),
    valid_until: date | None = None,
    case_id: str = "CASE-TEST-001",
    property_id: str = "PROPERTY-TEST-001",
    borrower_id: str | None = "BORROWER-TEST-001",
) -> EvidenceMetadata:
    valid_until = valid_until or evidence_date + timedelta(days=30)
    return EvidenceMetadata(
        evidence_id=evidence_id,
        observation_period=ObservationPeriod(evidence_date, evidence_date),
        published_at=datetime.combine(
            evidence_date, datetime.min.time(), tzinfo=timezone.utc
        ),
        retrieved_at=datetime.combine(
            evidence_date, datetime.min.time(), tzinfo=timezone.utc
        ),
        source_url=f"https://example.gov.cn/evidence/{evidence_id}",
        source_authority="Test Evidence Authority",
        kind=kind,
        role=role,
        region="中国/测试市/测试区",
        case_id=case_id,
        property_id=property_id,
        borrower_id=borrower_id,
        status=status,
        valid_from=evidence_date,
        valid_until=valid_until,
    )


def numeric(
    evidence_id: str,
    value: str,
    unit: Unit,
    status: EvidenceStatus = EvidenceStatus.VERIFIED,
    kind: EvidenceKind = EvidenceKind.TRANSACTION_INPUT,
    role: EvidenceRole = EvidenceRole.PURCHASE_PRICE,
    evidence_date: date = date(2026, 7, 1),
    valid_until: date | None = None,
    case_id: str = "CASE-TEST-001",
    property_id: str = "PROPERTY-TEST-001",
    borrower_id: str | None = "BORROWER-TEST-001",
) -> NumericEvidence:
    return NumericEvidence(
        evidence_id,
        Decimal(value),
        unit,
        metadata(
            evidence_id,
            status,
            kind,
            role,
            evidence_date,
            valid_until,
            case_id,
            property_id,
            borrower_id,
        ),
    )


def categorical(
    evidence_id: str,
    value: T,
    status: EvidenceStatus = EvidenceStatus.VERIFIED,
    kind: EvidenceKind = EvidenceKind.DUE_DILIGENCE_CHECK,
    role: EvidenceRole = EvidenceRole.TITLE_CHECK,
    evidence_date: date = date(2026, 7, 1),
    valid_until: date | None = None,
    case_id: str = "CASE-TEST-001",
    property_id: str = "PROPERTY-TEST-001",
    borrower_id: str | None = "BORROWER-TEST-001",
) -> CategoricalEvidence[T]:
    return CategoricalEvidence(
        evidence_id,
        value,
        metadata(
            evidence_id,
            status,
            kind,
            role,
            evidence_date,
            valid_until,
            case_id,
            property_id,
            borrower_id,
        ),
    )
