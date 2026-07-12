from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal

from core.contracts import (
    ContractError,
    EvidenceKind,
    EvidenceNotUsableError,
    EvidenceRole,
    EvidenceStatus,
    Unit,
)
from core.loan import LoanPayment, LoanSchedule, RepaymentMethod, build_loan_schedule
from tests.helpers import numeric


class LoanTests(unittest.TestCase):
    AS_OF = date(2026, 7, 12)

    def schedule(self, method: RepaymentMethod, rate: str = "0.048"):
        return build_loan_schedule(
            principal=numeric(
                "principal", "120000", Unit.CNY, role=EvidenceRole.LOAN_PRINCIPAL
            ),
            annual_rate=numeric(
                "contract-rate",
                rate,
                Unit.RATIO_PER_YEAR,
                kind=EvidenceKind.BANK_MORTGAGE_EXECUTION_QUOTE,
                role=EvidenceRole.BANK_MORTGAGE_EXECUTION_RATE,
                borrower_id="BORROWER-TEST-001",
            ),
            months=12,
            method=method,
            as_of=self.AS_OF,
        )

    def test_equal_payment_matches_standard_formula(self) -> None:
        result = self.schedule(RepaymentMethod.EQUAL_PAYMENT)
        self.assertEqual(12, len(result.payments))
        self.assertEqual("10261.90", str(result.payments[0].payment_cny))
        self.assertEqual("480.00", str(result.payments[0].interest_cny))
        self.assertEqual("0.00", str(result.payments[-1].remaining_principal_cny))
        self.assertEqual("3142.83", str(result.total_interest_cny))
        self.assertEqual("contract-rate", result.input_evidence[1].evidence_id)

    def test_equal_principal_payment_declines(self) -> None:
        result = self.schedule(RepaymentMethod.EQUAL_PRINCIPAL)
        self.assertEqual("10480.00", str(result.payments[0].payment_cny))
        self.assertEqual("10040.00", str(result.payments[-1].payment_cny))
        self.assertEqual("3120.00", str(result.total_interest_cny))
        self.assertGreater(
            result.payments[0].payment_cny, result.payments[-1].payment_cny
        )

    def test_zero_rate_is_supported_without_division_by_zero(self) -> None:
        result = self.schedule(RepaymentMethod.EQUAL_PAYMENT, "0")
        self.assertEqual("10000.00", str(result.payments[0].payment_cny))
        self.assertEqual("0.00", str(result.total_interest_cny))

    def test_tiny_nonzero_rate_is_refused_instead_of_miscalculated(self) -> None:
        with self.assertRaisesRegex(ContractError, "supported precision"):
            self.schedule(RepaymentMethod.EQUAL_PAYMENT, "1E-25")

    def test_unverified_rate_is_refused_instead_of_using_current_lpr(self) -> None:
        with self.assertRaises(EvidenceNotUsableError):
            build_loan_schedule(
                principal=numeric(
                    "principal",
                    "100000",
                    Unit.CNY,
                    role=EvidenceRole.LOAN_PRINCIPAL,
                ),
                annual_rate=numeric(
                    "claimed-lpr",
                    "0.03",
                    Unit.RATIO_PER_YEAR,
                    EvidenceStatus.UNVERIFIED,
                    EvidenceKind.BANK_MORTGAGE_EXECUTION_QUOTE,
                    EvidenceRole.BANK_MORTGAGE_EXECUTION_RATE,
                    borrower_id="BORROWER-TEST-001",
                ),
                months=12,
                method=RepaymentMethod.EQUAL_PAYMENT,
                as_of=self.AS_OF,
            )

    def test_rate_requires_annual_ratio_unit(self) -> None:
        with self.assertRaisesRegex(ContractError, "ratio/year"):
            build_loan_schedule(
                principal=numeric(
                    "principal", "100000", Unit.CNY, role=EvidenceRole.LOAN_PRINCIPAL
                ),
                annual_rate=numeric(
                    "rate",
                    "0.03",
                    Unit.RATIO,
                    kind=EvidenceKind.BANK_MORTGAGE_EXECUTION_QUOTE,
                    role=EvidenceRole.BANK_MORTGAGE_EXECUTION_RATE,
                    borrower_id="BORROWER-TEST-001",
                ),
                months=12,
                method=RepaymentMethod.EQUAL_PAYMENT,
                as_of=self.AS_OF,
            )

    def test_invalid_term_is_refused(self) -> None:
        for months in (0, -1, True):
            with self.subTest(months=months), self.assertRaises(ContractError):
                build_loan_schedule(
                    principal=numeric(
                        "principal",
                        "100000",
                        Unit.CNY,
                        role=EvidenceRole.LOAN_PRINCIPAL,
                    ),
                    annual_rate=numeric(
                        "rate",
                        "0.03",
                        Unit.RATIO_PER_YEAR,
                        kind=EvidenceKind.BANK_MORTGAGE_EXECUTION_QUOTE,
                        role=EvidenceRole.BANK_MORTGAGE_EXECUTION_RATE,
                        borrower_id="BORROWER-TEST-001",
                    ),
                    months=months,  # type: ignore[arg-type]
                    method=RepaymentMethod.EQUAL_PAYMENT,
                    as_of=self.AS_OF,
                )

    def test_verified_lpr_benchmark_is_not_a_bank_execution_quote(self) -> None:
        with self.assertRaisesRegex(EvidenceNotUsableError, "kind"):
            build_loan_schedule(
                principal=numeric(
                    "principal", "100000", Unit.CNY, role=EvidenceRole.LOAN_PRINCIPAL
                ),
                annual_rate=numeric(
                    "pbc-lpr-benchmark",
                    "0.035",
                    Unit.RATIO_PER_YEAR,
                    kind=EvidenceKind.MARKET_CONTEXT,
                    role=EvidenceRole.MARKET_CONTEXT_VALUE,
                ),
                months=12,
                method=RepaymentMethod.EQUAL_PAYMENT,
                as_of=self.AS_OF,
            )

    def test_bank_execution_quote_requires_borrower_scope(self) -> None:
        with self.assertRaisesRegex(ContractError, "borrower"):
            build_loan_schedule(
                principal=numeric(
                    "principal", "100000", Unit.CNY, role=EvidenceRole.LOAN_PRINCIPAL
                ),
                annual_rate=numeric(
                    "rate",
                    "0.03",
                    Unit.RATIO_PER_YEAR,
                    kind=EvidenceKind.BANK_MORTGAGE_EXECUTION_QUOTE,
                    role=EvidenceRole.BANK_MORTGAGE_EXECUTION_RATE,
                    borrower_id=None,
                ),
                months=12,
                method=RepaymentMethod.EQUAL_PAYMENT,
                as_of=self.AS_OF,
            )

    def test_cross_property_loan_evidence_is_refused(self) -> None:
        with self.assertRaisesRegex(ContractError, "one case and property"):
            build_loan_schedule(
                principal=numeric(
                    "principal", "100000", Unit.CNY, role=EvidenceRole.LOAN_PRINCIPAL
                ),
                annual_rate=numeric(
                    "rate",
                    "0.03",
                    Unit.RATIO_PER_YEAR,
                    kind=EvidenceKind.BANK_MORTGAGE_EXECUTION_QUOTE,
                    role=EvidenceRole.BANK_MORTGAGE_EXECUTION_RATE,
                    property_id="PROPERTY-OTHER",
                    borrower_id="BORROWER-TEST-001",
                ),
                months=12,
                method=RepaymentMethod.EQUAL_PAYMENT,
                as_of=self.AS_OF,
            )

    def test_cross_borrower_loan_evidence_is_refused(self) -> None:
        with self.assertRaisesRegex(ContractError, "same borrower"):
            build_loan_schedule(
                principal=numeric(
                    "principal", "100000", Unit.CNY, role=EvidenceRole.LOAN_PRINCIPAL
                ),
                annual_rate=numeric(
                    "rate",
                    "0.03",
                    Unit.RATIO_PER_YEAR,
                    kind=EvidenceKind.BANK_MORTGAGE_EXECUTION_QUOTE,
                    role=EvidenceRole.BANK_MORTGAGE_EXECUTION_RATE,
                    borrower_id="BORROWER-OTHER",
                ),
                months=12,
                method=RepaymentMethod.EQUAL_PAYMENT,
                as_of=self.AS_OF,
            )

    def test_schedule_cannot_be_reconstructed_with_tampered_totals(self) -> None:
        valid = self.schedule(RepaymentMethod.EQUAL_PAYMENT)
        with self.assertRaisesRegex(ContractError, "total payment"):
            LoanSchedule(
                method=valid.method,
                principal_cny=valid.principal_cny,
                annual_rate=valid.annual_rate,
                as_of=valid.as_of,
                months=valid.months,
                payments=valid.payments,
                total_payment_cny=valid.total_payment_cny + 1,
                total_interest_cny=valid.total_interest_cny,
                input_evidence=valid.input_evidence,
            )

    def test_schedule_rejects_tampered_rate_evidence(self) -> None:
        valid = self.schedule(RepaymentMethod.EQUAL_PAYMENT)
        tampered_rate = replace(valid.input_evidence[1], value="0.01")
        with self.assertRaisesRegex(ContractError, "rate evidence"):
            LoanSchedule(
                method=valid.method,
                principal_cny=valid.principal_cny,
                annual_rate=valid.annual_rate,
                as_of=valid.as_of,
                months=valid.months,
                payments=valid.payments,
                total_payment_cny=valid.total_payment_cny,
                total_interest_cny=valid.total_interest_cny,
                input_evidence=(valid.input_evidence[0], tampered_rate),
            )

    def test_schedule_rejects_rows_inconsistent_with_evidenced_rate(self) -> None:
        valid = self.schedule(RepaymentMethod.EQUAL_PRINCIPAL)
        forged = []
        remaining = valid.principal_cny
        principal = valid.principal_cny / Decimal(valid.months)
        for month in range(1, valid.months + 1):
            principal_part = remaining if month == valid.months else principal
            remaining -= principal_part
            forged.append(
                LoanPayment(
                    month=month,
                    payment_cny=principal_part,
                    principal_cny=principal_part,
                    interest_cny=Decimal("0"),
                    remaining_principal_cny=remaining,
                )
            )
        with self.assertRaisesRegex(ContractError, "evidenced rate"):
            LoanSchedule(
                method=valid.method,
                principal_cny=valid.principal_cny,
                annual_rate=valid.annual_rate,
                as_of=valid.as_of,
                months=valid.months,
                payments=tuple(forged),
                total_payment_cny=sum(row.payment_cny for row in forged),
                total_interest_cny=Decimal("0"),
                input_evidence=valid.input_evidence,
            )

    def test_schedule_rejects_invalid_payment_container(self) -> None:
        valid = self.schedule(RepaymentMethod.EQUAL_PAYMENT)
        with self.assertRaisesRegex(ContractError, "payments must be a tuple"):
            replace(valid, payments=None)  # type: ignore[arg-type]

    def test_schedule_rejects_invalid_reference_value(self) -> None:
        valid = self.schedule(RepaymentMethod.EQUAL_PAYMENT)
        with self.assertRaisesRegex(ContractError, "value"):
            replace(valid.input_evidence[1], value=None)  # type: ignore[arg-type]

    def test_fractional_cent_and_extreme_principal_are_refused(self) -> None:
        for amount in ("0.001", "100000.005", "1E+15"):
            with self.subTest(amount=amount), self.assertRaises(ContractError):
                build_loan_schedule(
                    principal=numeric(
                        "principal",
                        amount,
                        Unit.CNY,
                        role=EvidenceRole.LOAN_PRINCIPAL,
                    ),
                    annual_rate=numeric(
                        "rate",
                        "0.03",
                        Unit.RATIO_PER_YEAR,
                        kind=EvidenceKind.BANK_MORTGAGE_EXECUTION_QUOTE,
                        role=EvidenceRole.BANK_MORTGAGE_EXECUTION_RATE,
                    ),
                    months=12,
                    method=RepaymentMethod.EQUAL_PAYMENT,
                    as_of=self.AS_OF,
                )


if __name__ == "__main__":
    unittest.main()
