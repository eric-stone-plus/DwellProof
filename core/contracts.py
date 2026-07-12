"""Strict, source-aware input contracts for investment calculations.

The core deliberately does not accept bare numbers.  Every quantitative input
must retain the unit, observation window, publication/retrieval timestamps,
geography, source URL, and verification state needed to audit it later.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Generic, TypeVar
from urllib.parse import urlparse


class ContractError(ValueError):
    """Raised when an input does not satisfy the fail-closed contract."""


class EvidenceNotUsableError(ContractError):
    """Raised when evidence exists but is not verified for calculation."""


class EvidenceStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    STALE = "stale"
    CONFLICTED = "conflicted"
    MISSING = "missing"


class EvidenceKind(str, Enum):
    TRANSACTION_INPUT = "transaction_input"
    BANK_MORTGAGE_EXECUTION_QUOTE = "bank_mortgage_execution_quote"
    SCENARIO_ASSUMPTION = "scenario_assumption"
    DUE_DILIGENCE_CHECK = "due_diligence_check"
    OFFICIAL_POLICY = "official_policy"
    MARKET_CONTEXT = "market_context"


class EvidenceRole(str, Enum):
    PURCHASE_PRICE = "purchase_price"
    ACQUISITION_COSTS = "acquisition_costs"
    INITIAL_EQUITY = "initial_equity"
    MONTHLY_GROSS_RENT = "monthly_gross_rent"
    MONTHLY_FIXED_COSTS = "monthly_fixed_costs"
    VARIABLE_OPERATING_COST_RATE = "variable_operating_cost_rate"
    MONTHLY_RENT_GROWTH_RATE = "monthly_rent_growth_rate"
    MONTHLY_PROPERTY_GROWTH_RATE = "monthly_property_growth_rate"
    OCCUPANCY_RATE = "occupancy_rate"
    SALE_COST_RATE = "sale_cost_rate"
    MONTHLY_DISCOUNT_RATE = "monthly_discount_rate"
    LOAN_PRINCIPAL = "loan_principal"
    BANK_MORTGAGE_EXECUTION_RATE = "bank_mortgage_execution_rate"
    TAXABLE_PRICE = "taxable_price"
    FLOOR_AREA = "floor_area"
    HOUSEHOLD_HOME_COUNT = "household_home_count"
    TITLE_CHECK = "title_check"
    ENCUMBRANCE_CHECK = "encumbrance_check"
    PROPERTY_NATURE_CHECK = "property_nature_check"
    TENANCY_CHECK = "tenancy_check"
    TAX_CHECK = "tax_check"
    LOAN_CHECK = "loan_check"
    COMPARABLE_SALES_CHECK = "comparable_sales_check"
    POLICY_VALUE = "policy_value"
    MARKET_CONTEXT_VALUE = "market_context_value"


class Unit(str, Enum):
    CNY = "CNY"
    CNY_PER_MONTH = "CNY/month"
    SQUARE_METRE = "m2"
    RATIO = "ratio"
    RATIO_PER_YEAR = "ratio/year"
    RATIO_PER_MONTH = "ratio/month"


MAX_ABS_NUMERIC = Decimal("1e15")
MAX_CURRENCY_AMOUNT = Decimal("1e12")


def _has_cent_precision(value: Decimal) -> bool:
    if value == 0:
        return True
    digits = value.as_tuple().digits
    trailing_zeros = 0
    for digit in reversed(digits):
        if digit != 0:
            break
        trailing_zeros += 1
    return value.as_tuple().exponent + trailing_zeros >= -2


def validate_currency_amount(
    value: Decimal,
    field_name: str,
    *,
    allow_zero: bool = True,
    allow_negative: bool = False,
) -> None:
    """Validate a CNY amount without context-sensitive Decimal quantization."""

    if not isinstance(value, Decimal) or not value.is_finite():
        raise ContractError(f"{field_name} must be a finite Decimal")
    if abs(value) > MAX_CURRENCY_AMOUNT:
        raise ContractError(f"{field_name} exceeds the supported CNY range")
    if not _has_cent_precision(value):
        raise ContractError(f"{field_name} must not use fractions below one cent")
    if not allow_negative and value < 0:
        raise ContractError(f"{field_name} must not be negative")
    if not allow_zero and value == 0:
        raise ContractError(f"{field_name} must be positive")


@dataclass(frozen=True)
class ObservationPeriod:
    start: date
    end: date

    def __post_init__(self) -> None:
        if type(self.start) is not date or type(self.end) is not date:
            raise ContractError("observation period must use date values")
        if self.start > self.end:
            raise ContractError("observation period start must not follow end")


@dataclass(frozen=True)
class EvidenceMetadata:
    """Provenance shared by numeric and categorical evidence."""

    evidence_id: str
    observation_period: ObservationPeriod
    published_at: datetime
    retrieved_at: datetime
    source_url: str
    source_authority: str
    kind: EvidenceKind
    role: EvidenceRole
    region: str
    case_id: str
    property_id: str
    borrower_id: str | None
    status: EvidenceStatus
    valid_from: date
    valid_until: date

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_id, str) or not self.evidence_id.strip():
            raise ContractError("evidence_id is required")
        if not isinstance(self.observation_period, ObservationPeriod):
            raise ContractError("observation_period must be an ObservationPeriod")
        if not isinstance(self.status, EvidenceStatus):
            raise ContractError("status must be an EvidenceStatus")
        if not isinstance(self.kind, EvidenceKind):
            raise ContractError("kind must be an EvidenceKind")
        if not isinstance(self.role, EvidenceRole):
            raise ContractError("role must be an EvidenceRole")
        if (
            not isinstance(self.source_authority, str)
            or not self.source_authority.strip()
        ):
            raise ContractError("source_authority is required")
        if not isinstance(self.region, str) or not self.region.strip():
            raise ContractError("region is required")
        if not isinstance(self.case_id, str) or not self.case_id.strip():
            raise ContractError("case_id is required")
        if not isinstance(self.property_id, str) or not self.property_id.strip():
            raise ContractError("property_id is required")
        if self.borrower_id is not None and (
            not isinstance(self.borrower_id, str) or not self.borrower_id.strip()
        ):
            raise ContractError("borrower_id must be non-empty when supplied")
        for field_name, timestamp in (
            ("published_at", self.published_at),
            ("retrieved_at", self.retrieved_at),
        ):
            if not isinstance(timestamp, datetime) or timestamp.tzinfo is None:
                raise ContractError(f"{field_name} must be a timezone-aware datetime")
            if timestamp.utcoffset() is None:
                raise ContractError(f"{field_name} must have a valid UTC offset")
        if self.retrieved_at < self.published_at:
            raise ContractError("retrieved_at must not precede published_at")
        if self.observation_period.end > self.published_at.date():
            raise ContractError("observation period must not end after publication")
        if type(self.valid_from) is not date or type(self.valid_until) is not date:
            raise ContractError("validity window must use date values")
        if self.valid_from > self.valid_until:
            raise ContractError("valid_from must not follow valid_until")

        if not isinstance(self.source_url, str):
            raise ContractError("source_url must be a string")
        parsed = urlparse(self.source_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ContractError("source_url must be an absolute HTTP(S) URL")


@dataclass(frozen=True)
class NumericEvidence:
    name: str
    value: Decimal
    unit: Unit
    metadata: EvidenceMetadata

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ContractError("numeric evidence name is required")
        if not isinstance(self.value, Decimal):
            raise ContractError("numeric evidence value must be Decimal")
        if not self.value.is_finite():
            raise ContractError("numeric evidence value must be finite")
        if abs(self.value) > MAX_ABS_NUMERIC:
            raise ContractError("numeric evidence value exceeds the supported range")
        if not isinstance(self.unit, Unit):
            raise ContractError("unit must be a Unit")
        if self.unit in {Unit.CNY, Unit.CNY_PER_MONTH}:
            validate_currency_amount(
                self.value,
                "numeric evidence value",
                allow_negative=True,
            )
        if not isinstance(self.metadata, EvidenceMetadata):
            raise ContractError("metadata must be EvidenceMetadata")


T = TypeVar("T")


@dataclass(frozen=True)
class CategoricalEvidence(Generic[T]):
    name: str
    value: T
    metadata: EvidenceMetadata

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ContractError("categorical evidence name is required")
        if self.value is None:
            raise ContractError("categorical evidence value is required")
        if not isinstance(self.metadata, EvidenceMetadata):
            raise ContractError("metadata must be EvidenceMetadata")


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str
    name: str
    value: str
    unit: str
    observation_start: date
    observation_end: date
    published_at: datetime
    retrieved_at: datetime
    source_url: str
    source_authority: str
    kind: EvidenceKind
    role: EvidenceRole
    region: str
    case_id: str
    property_id: str
    borrower_id: str | None
    status: EvidenceStatus
    valid_from: date
    valid_until: date

    def __post_init__(self) -> None:
        for field_name, value in (
            ("evidence_id", self.evidence_id),
            ("name", self.name),
            ("value", self.value),
            ("unit", self.unit),
            ("source_url", self.source_url),
            ("source_authority", self.source_authority),
            ("region", self.region),
            ("case_id", self.case_id),
            ("property_id", self.property_id),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ContractError(f"evidence reference {field_name} is required")
        if self.borrower_id is not None and (
            not isinstance(self.borrower_id, str) or not self.borrower_id.strip()
        ):
            raise ContractError("evidence reference borrower_id is invalid")
        for field_name, value in (
            ("observation_start", self.observation_start),
            ("observation_end", self.observation_end),
            ("valid_from", self.valid_from),
            ("valid_until", self.valid_until),
        ):
            if type(value) is not date:
                raise ContractError(f"evidence reference {field_name} must be a date")
        if self.observation_start > self.observation_end:
            raise ContractError("evidence reference observation period is reversed")
        if self.valid_from > self.valid_until:
            raise ContractError("evidence reference validity window is reversed")
        for field_name, value in (
            ("published_at", self.published_at),
            ("retrieved_at", self.retrieved_at),
        ):
            if (
                not isinstance(value, datetime)
                or value.tzinfo is None
                or value.utcoffset() is None
            ):
                raise ContractError(
                    f"evidence reference {field_name} must be timezone-aware"
                )
        if self.retrieved_at < self.published_at:
            raise ContractError("evidence reference retrieval precedes publication")
        if not isinstance(self.kind, EvidenceKind):
            raise ContractError("evidence reference kind is invalid")
        if not isinstance(self.role, EvidenceRole):
            raise ContractError("evidence reference role is invalid")
        if not isinstance(self.status, EvidenceStatus):
            raise ContractError("evidence reference status is invalid")
        parsed = urlparse(self.source_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ContractError("evidence reference source URL is invalid")


def _require_usable_metadata(
    metadata: EvidenceMetadata,
    *,
    as_of: date,
    expected_kind: EvidenceKind | None = None,
    expected_role: EvidenceRole | None = None,
) -> None:
    if not isinstance(metadata, EvidenceMetadata):
        raise ContractError("metadata must be EvidenceMetadata")
    if expected_kind is not None and not isinstance(expected_kind, EvidenceKind):
        raise ContractError("expected_kind must be an EvidenceKind")
    if expected_role is not None and not isinstance(expected_role, EvidenceRole):
        raise ContractError("expected_role must be an EvidenceRole")
    if type(as_of) is not date:
        raise ContractError("as_of must be a date")
    if metadata.status is not EvidenceStatus.VERIFIED:
        raise EvidenceNotUsableError(
            f"evidence is {metadata.status.value}, not verified"
        )
    if expected_kind is not None and metadata.kind is not expected_kind:
        raise EvidenceNotUsableError(
            f"evidence kind is {metadata.kind.value}; expected {expected_kind.value}"
        )
    if expected_role is not None and metadata.role is not expected_role:
        raise EvidenceNotUsableError(
            f"evidence role is {metadata.role.value}; expected {expected_role.value}"
        )
    if metadata.observation_period.end > as_of:
        raise EvidenceNotUsableError("evidence observation period is after as_of")
    if metadata.published_at.date() > as_of:
        raise EvidenceNotUsableError("evidence publication is after as_of")
    if metadata.retrieved_at.date() > as_of:
        raise EvidenceNotUsableError("evidence retrieval is after as_of")
    if not metadata.valid_from <= as_of <= metadata.valid_until:
        raise EvidenceNotUsableError("evidence is outside its validity window")


def require_verified(
    evidence: NumericEvidence,
    expected_unit: Unit,
    *,
    as_of: date,
    expected_kind: EvidenceKind | None = None,
    expected_role: EvidenceRole | None = None,
) -> Decimal:
    """Return a value only when type, purpose and as-of validity are exact."""

    if not isinstance(evidence, NumericEvidence):
        raise ContractError("evidence must be NumericEvidence")
    if not isinstance(expected_unit, Unit):
        raise ContractError("expected_unit must be a Unit")
    _require_usable_metadata(
        evidence.metadata,
        as_of=as_of,
        expected_kind=expected_kind,
        expected_role=expected_role,
    )
    if evidence.unit is not expected_unit:
        raise ContractError(
            f"{evidence.name} has unit {evidence.unit.value}; expected {expected_unit.value}"
        )
    return evidence.value


def require_verified_category(
    evidence: CategoricalEvidence[T],
    *,
    as_of: date,
    expected_kind: EvidenceKind | None = None,
    expected_role: EvidenceRole | None = None,
) -> T:
    if not isinstance(evidence, CategoricalEvidence):
        raise ContractError("evidence must be CategoricalEvidence")
    _require_usable_metadata(
        evidence.metadata,
        as_of=as_of,
        expected_kind=expected_kind,
        expected_role=expected_role,
    )
    return evidence.value


def evidence_reference(evidence: NumericEvidence) -> EvidenceReference:
    if not isinstance(evidence, NumericEvidence):
        raise ContractError("evidence must be NumericEvidence")
    return EvidenceReference(
        evidence_id=evidence.metadata.evidence_id,
        name=evidence.name,
        value=str(evidence.value),
        unit=evidence.unit.value,
        observation_start=evidence.metadata.observation_period.start,
        observation_end=evidence.metadata.observation_period.end,
        published_at=evidence.metadata.published_at,
        retrieved_at=evidence.metadata.retrieved_at,
        source_url=evidence.metadata.source_url,
        source_authority=evidence.metadata.source_authority,
        kind=evidence.metadata.kind,
        role=evidence.metadata.role,
        region=evidence.metadata.region,
        case_id=evidence.metadata.case_id,
        property_id=evidence.metadata.property_id,
        borrower_id=evidence.metadata.borrower_id,
        status=evidence.metadata.status,
        valid_from=evidence.metadata.valid_from,
        valid_until=evidence.metadata.valid_until,
    )


def category_evidence_reference(
    evidence: CategoricalEvidence[object],
) -> EvidenceReference:
    if not isinstance(evidence, CategoricalEvidence):
        raise ContractError("evidence must be CategoricalEvidence")
    raw_value = getattr(evidence.value, "value", evidence.value)
    return EvidenceReference(
        evidence_id=evidence.metadata.evidence_id,
        name=evidence.name,
        value=str(raw_value),
        unit="categorical",
        observation_start=evidence.metadata.observation_period.start,
        observation_end=evidence.metadata.observation_period.end,
        published_at=evidence.metadata.published_at,
        retrieved_at=evidence.metadata.retrieved_at,
        source_url=evidence.metadata.source_url,
        source_authority=evidence.metadata.source_authority,
        kind=evidence.metadata.kind,
        role=evidence.metadata.role,
        region=evidence.metadata.region,
        case_id=evidence.metadata.case_id,
        property_id=evidence.metadata.property_id,
        borrower_id=evidence.metadata.borrower_id,
        status=evidence.metadata.status,
        valid_from=evidence.metadata.valid_from,
        valid_until=evidence.metadata.valid_until,
    )
