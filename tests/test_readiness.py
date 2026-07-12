from __future__ import annotations

import unittest
from datetime import date

from core.contracts import EvidenceRole, EvidenceStatus
from core.readiness import (
    CHECK_ROLES,
    REQUIRED_CHECKS,
    CheckName,
    CheckOutcome,
    evaluate_buy_readiness,
    guarded_decision,
)
from tests.helpers import categorical


def clear_checks():
    return {
        check: categorical(
            check.value, CheckOutcome.CLEAR, role=CHECK_ROLES[check]
        )
        for check in REQUIRED_CHECKS
    }


class ReadinessTests(unittest.TestCase):
    AS_OF = date(2026, 7, 12)

    def test_all_seven_verified_clear_checks_open_gate(self) -> None:
        result = evaluate_buy_readiness(clear_checks(), as_of=self.AS_OF)
        self.assertTrue(result.analysis_ready)
        self.assertEqual("ANALYSIS_READY", result.decision)
        self.assertEqual((), result.blockers)
        self.assertEqual(set(REQUIRED_CHECKS), set(result.passed_checks))
        self.assertEqual(7, len(result.evidence_ids))
        self.assertEqual(7, len(result.input_evidence))
        self.assertTrue(result.input_evidence[0].source_url.startswith("https://"))

    def test_each_missing_check_closes_gate(self) -> None:
        for missing in REQUIRED_CHECKS:
            with self.subTest(missing=missing):
                checks = clear_checks()
                del checks[missing]
                result = evaluate_buy_readiness(checks, as_of=self.AS_OF)
                self.assertFalse(result.analysis_ready)
                self.assertIn(f"{missing.value}:missing", result.blockers)

    def test_invalid_evidence_object_closes_gate_without_attribute_error(self) -> None:
        checks = clear_checks()
        checks[CheckName.TITLE] = "not evidence"  # type: ignore[assignment]
        result = evaluate_buy_readiness(checks, as_of=self.AS_OF)
        self.assertFalse(result.analysis_ready)
        self.assertIn("title:invalid_evidence", result.blockers)

    def test_unverified_check_closes_gate(self) -> None:
        checks = clear_checks()
        checks[CheckName.TAX] = categorical(
            "tax",
            CheckOutcome.CLEAR,
            EvidenceStatus.UNVERIFIED,
            role=EvidenceRole.TAX_CHECK,
        )
        result = evaluate_buy_readiness(checks, as_of=self.AS_OF)
        self.assertEqual("INSUFFICIENT_EVIDENCE", result.decision)
        self.assertTrue(
            any(blocker.startswith("tax:not_usable") for blocker in result.blockers)
        )

    def test_cross_property_checks_close_gate(self) -> None:
        checks = clear_checks()
        checks[CheckName.TAX] = categorical(
            CheckName.TAX.value,
            CheckOutcome.CLEAR,
            role=EvidenceRole.TAX_CHECK,
            property_id="PROPERTY-OTHER",
        )
        result = evaluate_buy_readiness(checks, as_of=self.AS_OF)
        self.assertFalse(result.analysis_ready)
        self.assertIn("evidence_scope:mismatch", result.blockers)

    def test_duplicate_evidence_id_closes_gate(self) -> None:
        checks = clear_checks()
        checks[CheckName.TAX] = categorical(
            CheckName.TAX.value,
            CheckOutcome.CLEAR,
            role=EvidenceRole.TAX_CHECK,
        )
        checks[CheckName.LOAN] = categorical(
            CheckName.LOAN.value,
            CheckOutcome.CLEAR,
            role=EvidenceRole.LOAN_CHECK,
        )
        checks[CheckName.COMPARABLE_SALES] = categorical(
            CheckName.LOAN.value,
            CheckOutcome.CLEAR,
            role=EvidenceRole.COMPARABLE_SALES_CHECK,
        )
        result = evaluate_buy_readiness(checks, as_of=self.AS_OF)
        self.assertFalse(result.analysis_ready)
        self.assertIn("evidence_id:duplicate", result.blockers)

    def test_cross_borrower_checks_close_gate(self) -> None:
        checks = clear_checks()
        checks[CheckName.LOAN] = categorical(
            CheckName.LOAN.value,
            CheckOutcome.CLEAR,
            role=EvidenceRole.LOAN_CHECK,
            borrower_id="BORROWER-OTHER",
        )
        result = evaluate_buy_readiness(checks, as_of=self.AS_OF)
        self.assertFalse(result.analysis_ready)
        self.assertIn("evidence_scope:mismatch", result.blockers)

    def test_missing_borrower_scope_closes_gate(self) -> None:
        checks = {
            check: categorical(
                check.value,
                CheckOutcome.CLEAR,
                role=CHECK_ROLES[check],
                borrower_id=None,
            )
            for check in REQUIRED_CHECKS
        }
        result = evaluate_buy_readiness(checks, as_of=self.AS_OF)
        self.assertFalse(result.analysis_ready)
        self.assertIn("borrower_id:missing", result.blockers)

    def test_adverse_and_unknown_checks_close_gate(self) -> None:
        for outcome in (CheckOutcome.ADVERSE, CheckOutcome.UNKNOWN):
            with self.subTest(outcome=outcome):
                checks = clear_checks()
                checks[CheckName.TITLE] = categorical(
                    "title", outcome, role=EvidenceRole.TITLE_CHECK
                )
                result = evaluate_buy_readiness(checks, as_of=self.AS_OF)
                self.assertFalse(result.analysis_ready)
                self.assertIn(f"title:{outcome.value}", result.blockers)

    def test_guard_suppresses_every_directional_label_when_closed(self) -> None:
        checks = clear_checks()
        del checks[CheckName.COMPARABLE_SALES]
        readiness = evaluate_buy_readiness(checks, as_of=self.AS_OF)
        for label in ("BUY", "STRONG_BUY", "SELL", "HOLD", "BEST_INVESTMENT"):
            with self.subTest(label=label):
                self.assertEqual(
                    "INSUFFICIENT_EVIDENCE", guarded_decision(label, readiness)
                )

    def test_guard_never_converts_readiness_into_a_directional_label(self) -> None:
        readiness = evaluate_buy_readiness(clear_checks(), as_of=self.AS_OF)
        for label in ("BUY", "SELL", "HOLD", "BEST_INVESTMENT"):
            with self.subTest(label=label):
                self.assertEqual("ANALYSIS_READY", guarded_decision(label, readiness))


if __name__ == "__main__":
    unittest.main()
