from __future__ import annotations

import unittest
from datetime import date

from core.contracts import (
    ContractError,
    EvidenceKind,
    EvidenceNotUsableError,
    EvidenceRole,
    EvidenceStatus,
    Unit,
)
from core.tax import (
    NATIONAL_DEED_TAX_RULE_ID,
    HouseholdHomeCount,
    TaxRuleNotSupportedError,
    calculate_national_deed_tax,
)
from tests.helpers import categorical, numeric


class TaxTests(unittest.TestCase):
    def calculate(self, area: str, count: HouseholdHomeCount):
        transaction_date = date(2024, 12, 1)
        return calculate_national_deed_tax(
            taxable_price=numeric(
                "tax-price",
                "1000000",
                Unit.CNY,
                role=EvidenceRole.TAXABLE_PRICE,
                evidence_date=transaction_date,
            ),
            floor_area=numeric(
                "area",
                area,
                Unit.SQUARE_METRE,
                role=EvidenceRole.FLOOR_AREA,
                evidence_date=transaction_date,
            ),
            household_home_count=categorical(
                "home-count",
                count,
                kind=EvidenceKind.TRANSACTION_INPUT,
                role=EvidenceRole.HOUSEHOLD_HOME_COUNT,
                evidence_date=transaction_date,
            ),
            transaction_date=transaction_date,
        )

    def test_only_home_140_boundary_is_inclusive_at_one_percent(self) -> None:
        result = self.calculate("140", HouseholdHomeCount.ONLY)
        self.assertEqual("0.01", str(result.rate))
        self.assertEqual("10000.00", str(result.tax_amount_cny))
        self.assertEqual(NATIONAL_DEED_TAX_RULE_ID, result.rule_id)
        self.assertTrue(result.official_source_url.startswith("https://"))

    def test_only_home_above_140_is_one_point_five_percent(self) -> None:
        result = self.calculate("140.0001", HouseholdHomeCount.ONLY)
        self.assertEqual("0.015", str(result.rate))

    def test_second_home_140_boundary_is_one_percent(self) -> None:
        self.assertEqual("0.01", str(self.calculate("140", HouseholdHomeCount.SECOND).rate))

    def test_second_home_above_140_is_two_percent(self) -> None:
        self.assertEqual("0.02", str(self.calculate("141", HouseholdHomeCount.SECOND).rate))

    def test_other_or_unknown_home_count_is_refused(self) -> None:
        with self.assertRaises(TaxRuleNotSupportedError):
            self.calculate("90", HouseholdHomeCount.OTHER)

    def test_transaction_before_rule_effective_date_is_refused(self) -> None:
        with self.assertRaises(TaxRuleNotSupportedError):
            calculate_national_deed_tax(
                taxable_price=numeric(
                    "price", "1", Unit.CNY,
                    role=EvidenceRole.TAXABLE_PRICE,
                    evidence_date=date(2024, 11, 30)
                ),
                floor_area=numeric(
                    "area", "90", Unit.SQUARE_METRE,
                    role=EvidenceRole.FLOOR_AREA,
                    evidence_date=date(2024, 11, 30)
                ),
                household_home_count=categorical(
                    "count",
                    HouseholdHomeCount.ONLY,
                    kind=EvidenceKind.TRANSACTION_INPUT,
                    role=EvidenceRole.HOUSEHOLD_HOME_COUNT,
                    evidence_date=date(2024, 11, 30),
                ),
                transaction_date=date(2024, 11, 30),
            )

    def test_unverified_price_is_refused(self) -> None:
        with self.assertRaises(EvidenceNotUsableError):
            calculate_national_deed_tax(
                taxable_price=numeric(
                    "price", "1000000", Unit.CNY, EvidenceStatus.UNVERIFIED,
                    role=EvidenceRole.TAXABLE_PRICE,
                    evidence_date=date(2025, 1, 1),
                ),
                floor_area=numeric(
                    "area", "90", Unit.SQUARE_METRE,
                    role=EvidenceRole.FLOOR_AREA,
                    evidence_date=date(2025, 1, 1)
                ),
                household_home_count=categorical(
                    "count",
                    HouseholdHomeCount.ONLY,
                    kind=EvidenceKind.TRANSACTION_INPUT,
                    role=EvidenceRole.HOUSEHOLD_HOME_COUNT,
                    evidence_date=date(2025, 1, 1),
                ),
                transaction_date=date(2025, 1, 1),
            )

    def test_wrong_area_unit_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "expected m2"):
            calculate_national_deed_tax(
                taxable_price=numeric(
                    "price", "1000000", Unit.CNY,
                    role=EvidenceRole.TAXABLE_PRICE,
                    evidence_date=date(2025, 1, 1)
                ),
                floor_area=numeric(
                    "area", "90", Unit.CNY,
                    role=EvidenceRole.FLOOR_AREA,
                    evidence_date=date(2025, 1, 1)
                ),
                household_home_count=categorical(
                    "count",
                    HouseholdHomeCount.ONLY,
                    kind=EvidenceKind.TRANSACTION_INPUT,
                    role=EvidenceRole.HOUSEHOLD_HOME_COUNT,
                    evidence_date=date(2025, 1, 1),
                ),
                transaction_date=date(2025, 1, 1),
            )

    def test_cross_property_tax_evidence_is_refused(self) -> None:
        transaction_date = date(2025, 1, 1)
        with self.assertRaisesRegex(ContractError, "one case"):
            calculate_national_deed_tax(
                taxable_price=numeric(
                    "price", "1000000", Unit.CNY,
                    role=EvidenceRole.TAXABLE_PRICE,
                    evidence_date=transaction_date
                ),
                floor_area=numeric(
                    "area",
                    "90",
                    Unit.SQUARE_METRE,
                    role=EvidenceRole.FLOOR_AREA,
                    evidence_date=transaction_date,
                    property_id="PROPERTY-OTHER",
                ),
                household_home_count=categorical(
                    "count",
                    HouseholdHomeCount.ONLY,
                    kind=EvidenceKind.TRANSACTION_INPUT,
                    role=EvidenceRole.HOUSEHOLD_HOME_COUNT,
                    evidence_date=transaction_date,
                ),
                transaction_date=transaction_date,
            )

    def test_missing_borrower_tax_evidence_is_refused(self) -> None:
        transaction_date = date(2025, 1, 1)
        with self.assertRaisesRegex(ContractError, "identify the borrower"):
            calculate_national_deed_tax(
                taxable_price=numeric(
                    "price",
                    "1000000",
                    Unit.CNY,
                    role=EvidenceRole.TAXABLE_PRICE,
                    evidence_date=transaction_date,
                    borrower_id=None,
                ),
                floor_area=numeric(
                    "area",
                    "90",
                    Unit.SQUARE_METRE,
                    role=EvidenceRole.FLOOR_AREA,
                    evidence_date=transaction_date,
                    borrower_id=None,
                ),
                household_home_count=categorical(
                    "count",
                    HouseholdHomeCount.ONLY,
                    kind=EvidenceKind.TRANSACTION_INPUT,
                    role=EvidenceRole.HOUSEHOLD_HOME_COUNT,
                    evidence_date=transaction_date,
                    borrower_id=None,
                ),
                transaction_date=transaction_date,
            )


if __name__ == "__main__":
    unittest.main()
