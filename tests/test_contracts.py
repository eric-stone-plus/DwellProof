from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

from core.contracts import (
    ContractError,
    EvidenceNotUsableError,
    EvidenceKind,
    EvidenceRole,
    EvidenceStatus,
    NumericEvidence,
    ObservationPeriod,
    Unit,
    require_verified,
)
from tests.helpers import metadata, numeric


class ContractTests(unittest.TestCase):
    def test_observation_period_rejects_reversed_dates(self) -> None:
        with self.assertRaisesRegex(ContractError, "start"):
            ObservationPeriod(date(2026, 2, 1), date(2026, 1, 1))

    def test_metadata_rejects_naive_timestamp(self) -> None:
        with self.assertRaisesRegex(ContractError, "timezone-aware"):
            replace(metadata("x"), retrieved_at=datetime(2026, 7, 1, 8, 0))

    def test_metadata_rejects_retrieval_before_publication(self) -> None:
        with self.assertRaisesRegex(ContractError, "must not precede"):
            replace(
                metadata("x"),
                retrieved_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
            )

    def test_metadata_rejects_non_http_source(self) -> None:
        with self.assertRaisesRegex(ContractError, "HTTP"):
            replace(metadata("x"), source_url="local-file.csv")

    def test_metadata_requires_source_authority(self) -> None:
        with self.assertRaisesRegex(ContractError, "source_authority"):
            replace(metadata("x"), source_authority=" ")

    def test_metadata_requires_case_and_property_scope(self) -> None:
        with self.assertRaisesRegex(ContractError, "case_id"):
            replace(metadata("x"), case_id=" ")
        with self.assertRaisesRegex(ContractError, "property_id"):
            replace(metadata("x"), property_id=" ")

    def test_datetime_is_not_accepted_as_a_date_contract(self) -> None:
        timestamp = datetime(2026, 7, 1, tzinfo=timezone.utc)
        with self.assertRaisesRegex(ContractError, "date values"):
            ObservationPeriod(timestamp, timestamp)  # type: ignore[arg-type]
        with self.assertRaisesRegex(ContractError, "as_of must be a date"):
            require_verified(
                numeric("price", "1", Unit.CNY),
                Unit.CNY,
                as_of=timestamp,  # type: ignore[arg-type]
            )

    def test_metadata_requires_observation_period_contract(self) -> None:
        with self.assertRaisesRegex(ContractError, "observation_period"):
            replace(metadata("x"), observation_period="2026-06")  # type: ignore[arg-type]

    def test_numeric_value_must_be_decimal(self) -> None:
        with self.assertRaisesRegex(ContractError, "Decimal"):
            NumericEvidence("price", 1, Unit.CNY, metadata("price"))  # type: ignore[arg-type]

    def test_numeric_value_must_be_finite(self) -> None:
        with self.assertRaisesRegex(ContractError, "finite"):
            NumericEvidence("price", Decimal("NaN"), Unit.CNY, metadata("price"))

    def test_numeric_value_range_and_currency_precision_are_bounded(self) -> None:
        with self.assertRaisesRegex(ContractError, "supported range"):
            numeric("huge", "1E+16", Unit.RATIO)
        with self.assertRaisesRegex(ContractError, "below one cent"):
            numeric("fractional-cent", "0.001", Unit.CNY)

    def test_require_verified_rejects_every_non_verified_state(self) -> None:
        for status in (
            EvidenceStatus.UNVERIFIED,
            EvidenceStatus.STALE,
            EvidenceStatus.CONFLICTED,
            EvidenceStatus.MISSING,
        ):
            with self.subTest(status=status), self.assertRaises(EvidenceNotUsableError):
                require_verified(
                    numeric("price", "1", Unit.CNY, status),
                    Unit.CNY,
                    as_of=date(2026, 7, 12),
                )

    def test_require_verified_rejects_wrong_unit(self) -> None:
        with self.assertRaisesRegex(ContractError, "expected CNY"):
            require_verified(
                numeric("area", "90", Unit.SQUARE_METRE),
                Unit.CNY,
                as_of=date(2026, 7, 12),
            )

    def test_require_verified_rejects_wrong_evidence_kind(self) -> None:
        with self.assertRaisesRegex(EvidenceNotUsableError, "kind"):
            require_verified(
                numeric(
                    "lpr",
                    "0.035",
                    Unit.RATIO_PER_YEAR,
                    kind=EvidenceKind.MARKET_CONTEXT,
                ),
                Unit.RATIO_PER_YEAR,
                as_of=date(2026, 7, 12),
                expected_kind=EvidenceKind.BANK_MORTGAGE_EXECUTION_QUOTE,
            )

    def test_require_verified_rejects_wrong_evidence_role(self) -> None:
        with self.assertRaisesRegex(EvidenceNotUsableError, "role"):
            require_verified(
                numeric(
                    "rent",
                    "3000",
                    Unit.CNY_PER_MONTH,
                    role=EvidenceRole.MONTHLY_GROSS_RENT,
                ),
                Unit.CNY_PER_MONTH,
                as_of=date(2026, 7, 12),
                expected_kind=EvidenceKind.TRANSACTION_INPUT,
                expected_role=EvidenceRole.MONTHLY_FIXED_COSTS,
            )

    def test_require_verified_rejects_future_and_expired_evidence(self) -> None:
        current = numeric("price", "1", Unit.CNY)
        with self.assertRaisesRegex(EvidenceNotUsableError, "validity"):
            require_verified(current, Unit.CNY, as_of=date(2026, 8, 1))

        future = replace(
            current,
            metadata=replace(
                current.metadata,
                observation_period=ObservationPeriod(
                    date(2026, 7, 13), date(2026, 7, 13)
                ),
                published_at=datetime(2026, 7, 13, 8, 0, tzinfo=timezone.utc),
                retrieved_at=datetime(2026, 7, 13, 9, 0, tzinfo=timezone.utc),
                valid_from=date(2026, 7, 13),
            ),
        )
        with self.assertRaisesRegex(EvidenceNotUsableError, "after as_of"):
            require_verified(future, Unit.CNY, as_of=date(2026, 7, 12))


if __name__ == "__main__":
    unittest.main()
