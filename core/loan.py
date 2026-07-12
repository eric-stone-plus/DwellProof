"""Basic fixed-rate mortgage schedules.

No LPR or spread is embedded.  The caller must provide a verified annual rate
with provenance, because the applicable rate depends on lender, borrower,
property, date, and contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, localcontext
from enum import Enum

from .contracts import (
    ContractError,
    EvidenceKind,
    EvidenceReference,
    EvidenceRole,
    EvidenceStatus,
    NumericEvidence,
    Unit,
    evidence_reference,
    require_verified,
    validate_currency_amount,
)


CENT = Decimal("0.01")
MIN_NONZERO_ANNUAL_RATE = Decimal("1e-12")


class RepaymentMethod(str, Enum):
    EQUAL_PAYMENT = "equal_principal_and_interest"
    EQUAL_PRINCIPAL = "equal_principal"


@dataclass(frozen=True)
class LoanPayment:
    month: int
    payment_cny: Decimal
    principal_cny: Decimal
    interest_cny: Decimal
    remaining_principal_cny: Decimal


@dataclass(frozen=True)
class LoanSchedule:
    method: RepaymentMethod
    principal_cny: Decimal
    annual_rate: Decimal
    as_of: date
    months: int
    payments: tuple[LoanPayment, ...]
    total_payment_cny: Decimal
    total_interest_cny: Decimal
    input_evidence: tuple[EvidenceReference, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.method, RepaymentMethod):
            raise ContractError("loan schedule method is invalid")
        validate_currency_amount(
            self.principal_cny,
            "loan schedule principal",
            allow_zero=False,
        )
        if (
            not isinstance(self.annual_rate, Decimal)
            or not self.annual_rate.is_finite()
            or self.annual_rate < 0
            or self.annual_rate >= 1
        ):
            raise ContractError("loan schedule annual rate must be in [0, 1)")
        if 0 < self.annual_rate < MIN_NONZERO_ANNUAL_RATE:
            raise ContractError("non-zero annual loan rate is below supported precision")
        if (
            isinstance(self.months, bool)
            or not isinstance(self.months, int)
            or self.months <= 0
        ):
            raise ContractError("loan schedule months must be a positive integer")
        if not isinstance(self.payments, tuple):
            raise ContractError("loan schedule payments must be a tuple")
        if any(not isinstance(payment, LoanPayment) for payment in self.payments):
            raise ContractError("loan schedule payments must contain LoanPayment rows")
        if len(self.payments) != self.months:
            raise ContractError("loan schedule must contain exactly one row per month")
        if type(self.as_of) is not date:
            raise ContractError("loan schedule as_of must be a date")
        if not isinstance(self.input_evidence, tuple):
            raise ContractError("loan schedule input_evidence must be a tuple")
        if any(
            not isinstance(item, EvidenceReference) for item in self.input_evidence
        ):
            raise ContractError("loan schedule evidence rows are invalid")
        if len(self.input_evidence) != 2 or any(
            item.status is not EvidenceStatus.VERIFIED for item in self.input_evidence
        ):
            raise ContractError("loan schedule requires verified principal and rate evidence")
        expected_kinds = (
            EvidenceKind.TRANSACTION_INPUT,
            EvidenceKind.BANK_MORTGAGE_EXECUTION_QUOTE,
        )
        for item, expected_kind in zip(self.input_evidence, expected_kinds):
            if item.kind is not expected_kind:
                raise ContractError("loan schedule evidence kind is invalid")
            if not item.valid_from <= self.as_of <= item.valid_until:
                raise ContractError("loan schedule evidence is invalid at as_of")
            if max(
                item.observation_end,
                item.published_at.date(),
                item.retrieved_at.date(),
            ) > self.as_of:
                raise ContractError("loan schedule evidence is from after as_of")
        principal_reference, rate_reference = self.input_evidence
        if principal_reference.evidence_id == rate_reference.evidence_id:
            raise ContractError("loan evidence IDs must be unique")
        if (
            principal_reference.case_id != rate_reference.case_id
            or principal_reference.property_id != rate_reference.property_id
        ):
            raise ContractError("loan evidence must share one case and property")
        if (
            principal_reference.role is not EvidenceRole.LOAN_PRINCIPAL
            or rate_reference.role
            is not EvidenceRole.BANK_MORTGAGE_EXECUTION_RATE
        ):
            raise ContractError("loan evidence role is invalid")
        if (
            not principal_reference.borrower_id
            or principal_reference.borrower_id != rate_reference.borrower_id
        ):
            raise ContractError(
                "loan principal and bank execution quote must identify the same borrower"
            )
        try:
            evidenced_principal = Decimal(principal_reference.value)
            evidenced_rate = Decimal(rate_reference.value)
        except (ValueError, TypeError, ArithmeticError) as exc:
            raise ContractError("loan evidence value must be numeric") from exc
        if (
            principal_reference.unit != Unit.CNY.value
            or evidenced_principal != self.principal_cny
        ):
            raise ContractError("loan principal evidence does not match schedule")
        if (
            rate_reference.unit != Unit.RATIO_PER_YEAR.value
            or evidenced_rate != self.annual_rate
        ):
            raise ContractError("loan rate evidence does not match schedule")

        previous_balance = _money(self.principal_cny)
        monthly_rate = self.annual_rate / Decimal(12)
        expected_equal_payment = None
        if self.method is RepaymentMethod.EQUAL_PAYMENT:
            expected_equal_payment = _money(
                _equal_payment_amount(
                    self.principal_cny,
                    self.annual_rate,
                    self.months,
                )
            )
        expected_regular_principal = _money(
            self.principal_cny / Decimal(self.months)
        )
        for expected_month, payment in enumerate(self.payments, start=1):
            for amount in (
                payment.payment_cny,
                payment.principal_cny,
                payment.interest_cny,
                payment.remaining_principal_cny,
            ):
                if not isinstance(amount, Decimal) or not amount.is_finite():
                    raise ContractError("loan schedule amounts must be finite Decimals")
                validate_currency_amount(amount, "loan schedule amount")
            if payment.month != expected_month:
                raise ContractError("loan schedule months must be consecutive")
            if min(
                payment.payment_cny,
                payment.principal_cny,
                payment.interest_cny,
                payment.remaining_principal_cny,
            ) < 0:
                raise ContractError("loan schedule amounts must not be negative")
            if payment.payment_cny != payment.principal_cny + payment.interest_cny:
                raise ContractError("loan payment must equal principal plus interest")
            expected_interest = _money(previous_balance * monthly_rate)
            if payment.interest_cny != expected_interest:
                raise ContractError("loan interest does not match the evidenced rate")
            is_final = expected_month == self.months
            if self.method is RepaymentMethod.EQUAL_PAYMENT:
                expected_payment = (
                    previous_balance + expected_interest
                    if is_final
                    else expected_equal_payment
                )
                if payment.payment_cny != expected_payment:
                    raise ContractError("equal-payment row does not match the method")
            else:
                expected_principal = (
                    previous_balance if is_final else expected_regular_principal
                )
                if payment.principal_cny != expected_principal:
                    raise ContractError("equal-principal row does not match the method")
            if payment.remaining_principal_cny != _money(
                previous_balance - payment.principal_cny
            ):
                raise ContractError("loan schedule balance does not reconcile")
            previous_balance = payment.remaining_principal_cny
        if previous_balance != 0:
            raise ContractError("loan schedule must fully amortize by its final month")
        if self.total_payment_cny != sum(
            payment.payment_cny for payment in self.payments
        ):
            raise ContractError("loan schedule total payment does not reconcile")
        if self.total_interest_cny != sum(
            payment.interest_cny for payment in self.payments
        ):
            raise ContractError("loan schedule total interest does not reconcile")


def _money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def _equal_payment_amount(
    principal: Decimal,
    annual_rate: Decimal,
    months: int,
) -> Decimal:
    """Compute the annuity payment without low-rate cancellation."""

    if annual_rate == 0:
        return principal / Decimal(months)
    if annual_rate < MIN_NONZERO_ANNUAL_RATE:
        raise ContractError("non-zero annual loan rate is below supported precision")
    try:
        with localcontext() as context:
            context.prec = 50
            monthly_rate = annual_rate / Decimal(12)
            factor = (Decimal(1) + monthly_rate) ** months
            return principal * monthly_rate * factor / (factor - Decimal(1))
    except ArithmeticError as exc:
        raise ContractError("equal-payment loan calculation is unsupported") from exc


def build_loan_schedule(
    *,
    principal: NumericEvidence,
    annual_rate: NumericEvidence,
    months: int,
    method: RepaymentMethod,
    as_of: date,
) -> LoanSchedule:
    """Build a monthly fixed-rate schedule from verified caller inputs."""

    if type(as_of) is not date:
        raise ContractError("as_of must be a date")
    amount = require_verified(
        principal,
        Unit.CNY,
        as_of=as_of,
        expected_kind=EvidenceKind.TRANSACTION_INPUT,
        expected_role=EvidenceRole.LOAN_PRINCIPAL,
    )
    yearly_rate = require_verified(
        annual_rate,
        Unit.RATIO_PER_YEAR,
        as_of=as_of,
        expected_kind=EvidenceKind.BANK_MORTGAGE_EXECUTION_QUOTE,
        expected_role=EvidenceRole.BANK_MORTGAGE_EXECUTION_RATE,
    )
    if amount <= 0:
        raise ContractError("loan principal must be positive")
    validate_currency_amount(amount, "loan principal", allow_zero=False)
    if yearly_rate < 0 or yearly_rate >= 1:
        raise ContractError("annual loan rate must be in [0, 1)")
    if 0 < yearly_rate < MIN_NONZERO_ANNUAL_RATE:
        raise ContractError("non-zero annual loan rate is below supported precision")
    if isinstance(months, bool) or not isinstance(months, int) or months <= 0:
        raise ContractError("loan months must be a positive integer")
    if not isinstance(method, RepaymentMethod):
        raise ContractError("method must be a RepaymentMethod")

    monthly_rate = yearly_rate / Decimal(12)
    remaining = _money(amount)
    payments: list[LoanPayment] = []

    if method is RepaymentMethod.EQUAL_PAYMENT:
        exact_payment = _equal_payment_amount(amount, yearly_rate, months)

        for month in range(1, months + 1):
            interest = _money(remaining * monthly_rate)
            if month == months:
                principal_part = remaining
                month_payment = principal_part + interest
            else:
                month_payment = _money(exact_payment)
                principal_part = month_payment - interest
            remaining = _money(remaining - principal_part)
            payments.append(
                LoanPayment(
                    month=month,
                    payment_cny=month_payment,
                    principal_cny=principal_part,
                    interest_cny=interest,
                    remaining_principal_cny=max(remaining, Decimal(0)),
                )
            )
    else:
        regular_principal = _money(amount / Decimal(months))
        for month in range(1, months + 1):
            principal_part = remaining if month == months else regular_principal
            interest = _money(remaining * monthly_rate)
            payment = principal_part + interest
            remaining = _money(remaining - principal_part)
            payments.append(
                LoanPayment(
                    month=month,
                    payment_cny=payment,
                    principal_cny=principal_part,
                    interest_cny=interest,
                    remaining_principal_cny=max(remaining, Decimal(0)),
                )
            )

    return LoanSchedule(
        method=method,
        principal_cny=amount,
        annual_rate=yearly_rate,
        as_of=as_of,
        months=months,
        payments=tuple(payments),
        total_payment_cny=_money(sum(p.payment_cny for p in payments)),
        total_interest_cny=_money(sum(p.interest_cny for p in payments)),
        input_evidence=(evidence_reference(principal), evidence_reference(annual_rate)),
    )
