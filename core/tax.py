"""Versioned national deed-tax rules with explicit unsupported-case refusal."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from .contracts import (
    CategoricalEvidence,
    ContractError,
    EvidenceKind,
    EvidenceReference,
    EvidenceRole,
    NumericEvidence,
    Unit,
    category_evidence_reference,
    evidence_reference,
    require_verified,
    require_verified_category,
    validate_currency_amount,
)


class TaxRuleNotSupportedError(ContractError):
    """Raised when no verified, implemented rule may be applied."""


class HouseholdHomeCount(str, Enum):
    ONLY = "only_home"
    SECOND = "second_home"
    OTHER = "other_or_unknown"


NATIONAL_DEED_TAX_RULE_ID = "CN-DEED-TAX-2024-12-01-v1"
NATIONAL_DEED_TAX_EFFECTIVE_FROM = date(2024, 12, 1)
NATIONAL_DEED_TAX_SOURCE_URL = (
    "https://guangdong.chinatax.gov.cn/gdsw/zjfg/2024-11/14/"
    "content_0289c52475614b0c9d89145c43310721.shtml"
)


@dataclass(frozen=True)
class DeedTaxResult:
    tax_amount_cny: Decimal
    taxable_price_cny: Decimal
    rate: Decimal
    rule_id: str
    effective_from: date
    official_source_url: str
    input_evidence: tuple[EvidenceReference, ...]


def calculate_national_deed_tax(
    *,
    taxable_price: NumericEvidence,
    floor_area: NumericEvidence,
    household_home_count: CategoricalEvidence[HouseholdHomeCount],
    transaction_date: date,
) -> DeedTaxResult:
    """Calculate the buyer's preferential deed tax under announcement No. 16.

    The 140 m2 threshold is inclusive.  Third-or-later homes, unknown household
    counts, transactions before the effective date, and unverified evidence are
    rejected instead of guessed.
    """

    if type(transaction_date) is not date:
        raise ContractError("transaction_date must be a date")
    if transaction_date < NATIONAL_DEED_TAX_EFFECTIVE_FROM:
        raise TaxRuleNotSupportedError(
            "transaction predates implemented deed-tax rule version"
        )

    price = require_verified(
        taxable_price,
        Unit.CNY,
        as_of=transaction_date,
        expected_kind=EvidenceKind.TRANSACTION_INPUT,
        expected_role=EvidenceRole.TAXABLE_PRICE,
    )
    area = require_verified(
        floor_area,
        Unit.SQUARE_METRE,
        as_of=transaction_date,
        expected_kind=EvidenceKind.TRANSACTION_INPUT,
        expected_role=EvidenceRole.FLOOR_AREA,
    )
    home_count = require_verified_category(
        household_home_count,
        as_of=transaction_date,
        expected_kind=EvidenceKind.TRANSACTION_INPUT,
        expected_role=EvidenceRole.HOUSEHOLD_HOME_COUNT,
    )
    scopes = {
        (
            evidence.metadata.case_id,
            evidence.metadata.property_id,
            evidence.metadata.borrower_id,
        )
        for evidence in (taxable_price, floor_area, household_home_count)
    }
    if len(scopes) != 1:
        raise ContractError(
            "deed-tax evidence must share one case, property, and borrower"
        )
    if any(
        not evidence.metadata.borrower_id
        for evidence in (taxable_price, floor_area, household_home_count)
    ):
        raise ContractError("deed-tax evidence must identify the borrower")
    evidence_ids = {
        taxable_price.metadata.evidence_id,
        floor_area.metadata.evidence_id,
        household_home_count.metadata.evidence_id,
    }
    if len(evidence_ids) != 3:
        raise ContractError("deed-tax evidence IDs must be unique")
    if price <= 0:
        raise ContractError("taxable price must be positive")
    validate_currency_amount(price, "taxable price", allow_zero=False)
    if area <= 0:
        raise ContractError("floor area must be positive")
    if not isinstance(home_count, HouseholdHomeCount):
        raise TaxRuleNotSupportedError("household home count is invalid")

    if home_count is HouseholdHomeCount.ONLY:
        rate = Decimal("0.01") if area <= Decimal("140") else Decimal("0.015")
    elif home_count is HouseholdHomeCount.SECOND:
        rate = Decimal("0.01") if area <= Decimal("140") else Decimal("0.02")
    else:
        raise TaxRuleNotSupportedError(
            "no preferential rule implemented for other or unknown home count"
        )

    try:
        amount = (price * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except ArithmeticError as exc:
        raise ContractError("deed-tax amount is outside the supported range") from exc
    return DeedTaxResult(
        tax_amount_cny=amount,
        taxable_price_cny=price,
        rate=rate,
        rule_id=NATIONAL_DEED_TAX_RULE_ID,
        effective_from=NATIONAL_DEED_TAX_EFFECTIVE_FROM,
        official_source_url=NATIONAL_DEED_TAX_SOURCE_URL,
        input_evidence=(
            evidence_reference(taxable_price),
            evidence_reference(floor_area),
            category_evidence_reference(household_home_count),
        ),
    )
