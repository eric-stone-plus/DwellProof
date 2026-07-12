"""Monthly holding-period cash flow and scenario metrics.

The model is a deterministic calculator, not a forecast.  It applies explicit
scenario assumptions to verified base inputs, includes acquisition/sale cash,
rent, recurring expenses and debt service, and leaves all omitted taxes or
local charges visible as caller-owned inputs rather than silently estimating.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

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
from .loan import LoanSchedule
from .readiness import CHECK_ROLES, REQUIRED_CHECKS, ReadinessResult


@dataclass(frozen=True)
class ScenarioAssumptions:
    name: str
    monthly_rent_growth_rate: NumericEvidence
    monthly_property_growth_rate: NumericEvidence
    occupancy_rate: NumericEvidence
    sale_cost_rate: NumericEvidence
    monthly_discount_rate: NumericEvidence


@dataclass(frozen=True)
class CashFlowInputs:
    purchase_price: NumericEvidence
    acquisition_costs: NumericEvidence
    initial_equity: NumericEvidence
    monthly_gross_rent: NumericEvidence
    monthly_fixed_costs: NumericEvidence
    variable_operating_cost_rate: NumericEvidence
    holding_months: int
    loan_schedule: LoanSchedule | None = None


@dataclass(frozen=True)
class MonthlyCashFlow:
    month: int
    gross_rent_cny: Decimal
    effective_rent_cny: Decimal
    operating_costs_cny: Decimal
    debt_service_cny: Decimal
    sale_proceeds_cny: Decimal
    net_cash_flow_cny: Decimal
    cumulative_cash_flow_cny: Decimal


@dataclass(frozen=True)
class ScenarioResult:
    scenario: str
    monthly_cash_flows: tuple[MonthlyCashFlow, ...]
    net_rental_yield: Decimal
    monthly_irr: Decimal | None
    annualized_irr: Decimal | None
    npv_cny: Decimal
    maximum_cash_shortfall_cny: Decimal
    ending_property_value_cny: Decimal
    ending_loan_balance_cny: Decimal
    input_evidence: tuple[EvidenceReference, ...]


def _ratio(
    evidence: NumericEvidence, *, role: EvidenceRole, as_of: date
) -> Decimal:
    value = require_verified(
        evidence,
        Unit.RATIO,
        as_of=as_of,
        expected_kind=EvidenceKind.SCENARIO_ASSUMPTION,
        expected_role=role,
    )
    if value < 0 or value > 1:
        raise ContractError(f"{evidence.name} must be in [0, 1]")
    return value


def _monthly_rate(
    evidence: NumericEvidence,
    *,
    role: EvidenceRole,
    allow_negative: bool,
    as_of: date,
) -> Decimal:
    value = require_verified(
        evidence,
        Unit.RATIO_PER_MONTH,
        as_of=as_of,
        expected_kind=EvidenceKind.SCENARIO_ASSUMPTION,
        expected_role=role,
    )
    below_floor = value <= Decimal("-1") if allow_negative else value < Decimal(0)
    if below_floor or value >= 1:
        bracket = "(-1, 1)" if allow_negative else "[0, 1)"
        raise ContractError(f"{evidence.name} must be in {bracket}")
    return value


def _irr(cash_flows: list[Decimal]) -> Decimal | None:
    """Return the unique practical monthly IRR, or None if it cannot be bracketed."""

    if not any(value < 0 for value in cash_flows) or not any(
        value > 0 for value in cash_flows
    ):
        return None
    signs = [value > 0 for value in cash_flows if value != 0]
    if sum(left != right for left, right in zip(signs, signs[1:])) != 1:
        return None

    def npv(rate: Decimal) -> Decimal:
        base = Decimal(1) + rate
        return sum(value / (base**month) for month, value in enumerate(cash_flows))

    low = Decimal("-0.999999")
    high = Decimal("1")
    low_value = npv(low)
    high_value = npv(high)
    if low_value == 0:
        return low
    if high_value == 0:
        return high
    if low_value * high_value > 0:
        return None
    for _ in range(160):
        middle = (low + high) / Decimal(2)
        middle_value = npv(middle)
        if abs(middle_value) < Decimal("0.000001"):
            return middle
        if low_value * middle_value <= 0:
            high = middle
        else:
            low = middle
            low_value = middle_value
    return (low + high) / Decimal(2)


def analyze_scenario(
    inputs: CashFlowInputs,
    scenario: ScenarioAssumptions,
    *,
    readiness: ReadinessResult,
    as_of: date,
) -> ScenarioResult:
    """Calculate one complete monthly holding-period scenario."""

    if not isinstance(inputs, CashFlowInputs):
        raise ContractError("inputs must be CashFlowInputs")
    if not isinstance(scenario, ScenarioAssumptions):
        raise ContractError("scenario must be ScenarioAssumptions")
    if type(as_of) is not date:
        raise ContractError("as_of must be a date")
    if not isinstance(scenario.name, str) or not scenario.name.strip():
        raise ContractError("scenario name is required")
    if not isinstance(readiness, ReadinessResult) or not readiness.analysis_ready:
        raise ContractError("cash-flow analysis requires an open readiness gate")
    if readiness.evaluated_as_of != as_of:
        raise ContractError("readiness and cash-flow as_of dates must match")
    if readiness.decision != "ANALYSIS_READY" or readiness.blockers:
        raise ContractError("readiness result invariants are invalid")
    if (
        len(readiness.input_evidence) != 7
        or len(set(readiness.evidence_ids)) != 7
        or set(readiness.passed_checks) != set(REQUIRED_CHECKS)
        or readiness.passed_checks != REQUIRED_CHECKS
        or readiness.evidence_ids
        != tuple(item.evidence_id for item in readiness.input_evidence)
    ):
        raise ContractError("readiness must contain seven unique evidence checks")
    for check, item in zip(REQUIRED_CHECKS, readiness.input_evidence):
        if (
            item.name != check.value
            or item.role is not CHECK_ROLES[check]
            or item.value != "clear"
            or
            item.status is not EvidenceStatus.VERIFIED
            or item.kind is not EvidenceKind.DUE_DILIGENCE_CHECK
            or not item.valid_from <= as_of <= item.valid_until
            or max(
                item.observation_end,
                item.published_at.date(),
                item.retrieved_at.date(),
            )
            > as_of
        ):
            raise ContractError("readiness evidence is not usable at as_of")
    purchase = require_verified(
        inputs.purchase_price,
        Unit.CNY,
        as_of=as_of,
        expected_kind=EvidenceKind.TRANSACTION_INPUT,
        expected_role=EvidenceRole.PURCHASE_PRICE,
    )
    acquisition = require_verified(
        inputs.acquisition_costs,
        Unit.CNY,
        as_of=as_of,
        expected_kind=EvidenceKind.TRANSACTION_INPUT,
        expected_role=EvidenceRole.ACQUISITION_COSTS,
    )
    initial_equity = require_verified(
        inputs.initial_equity,
        Unit.CNY,
        as_of=as_of,
        expected_kind=EvidenceKind.TRANSACTION_INPUT,
        expected_role=EvidenceRole.INITIAL_EQUITY,
    )
    base_rent = require_verified(
        inputs.monthly_gross_rent,
        Unit.CNY_PER_MONTH,
        as_of=as_of,
        expected_kind=EvidenceKind.TRANSACTION_INPUT,
        expected_role=EvidenceRole.MONTHLY_GROSS_RENT,
    )
    fixed_cost = require_verified(
        inputs.monthly_fixed_costs,
        Unit.CNY_PER_MONTH,
        as_of=as_of,
        expected_kind=EvidenceKind.TRANSACTION_INPUT,
        expected_role=EvidenceRole.MONTHLY_FIXED_COSTS,
    )
    variable_cost_rate = _ratio(
        inputs.variable_operating_cost_rate,
        role=EvidenceRole.VARIABLE_OPERATING_COST_RATE,
        as_of=as_of,
    )
    occupancy = _ratio(
        scenario.occupancy_rate, role=EvidenceRole.OCCUPANCY_RATE, as_of=as_of
    )
    sale_cost_rate = _ratio(
        scenario.sale_cost_rate, role=EvidenceRole.SALE_COST_RATE, as_of=as_of
    )
    rent_growth = _monthly_rate(
        scenario.monthly_rent_growth_rate,
        role=EvidenceRole.MONTHLY_RENT_GROWTH_RATE,
        allow_negative=True,
        as_of=as_of,
    )
    property_growth = _monthly_rate(
        scenario.monthly_property_growth_rate,
        role=EvidenceRole.MONTHLY_PROPERTY_GROWTH_RATE,
        allow_negative=True,
        as_of=as_of,
    )
    discount_rate = _monthly_rate(
        scenario.monthly_discount_rate,
        role=EvidenceRole.MONTHLY_DISCOUNT_RATE,
        allow_negative=False,
        as_of=as_of,
    )

    all_numeric_evidence = (
        inputs.purchase_price,
        inputs.acquisition_costs,
        inputs.initial_equity,
        inputs.monthly_gross_rent,
        inputs.monthly_fixed_costs,
        inputs.variable_operating_cost_rate,
        scenario.monthly_rent_growth_rate,
        scenario.monthly_property_growth_rate,
        scenario.occupancy_rate,
        scenario.sale_cost_rate,
        scenario.monthly_discount_rate,
    )
    scope = {
        (
            item.metadata.case_id,
            item.metadata.property_id,
            item.metadata.borrower_id,
        )
        for item in all_numeric_evidence
    }
    scope.update(
        (item.case_id, item.property_id, item.borrower_id)
        for item in readiness.input_evidence
    )
    if inputs.loan_schedule is not None and not isinstance(
        inputs.loan_schedule, LoanSchedule
    ):
        raise ContractError("loan_schedule must be LoanSchedule or None")
    if inputs.loan_schedule:
        scope.update(
            (item.case_id, item.property_id, item.borrower_id)
            for item in inputs.loan_schedule.input_evidence
        )
    if len(scope) != 1:
        raise ContractError(
            "all evidence must share one case, property, and borrower"
        )
    if any(not item.metadata.borrower_id for item in all_numeric_evidence) or any(
        not item.borrower_id for item in readiness.input_evidence
    ):
        raise ContractError("all cash-flow evidence must identify the borrower")

    if purchase <= 0 or initial_equity <= 0:
        raise ContractError("purchase price and initial equity must be positive")
    if acquisition < 0 or base_rent < 0 or fixed_cost < 0:
        raise ContractError("cost and rent inputs must not be negative")
    validate_currency_amount(purchase, "purchase price", allow_zero=False)
    validate_currency_amount(acquisition, "acquisition costs")
    validate_currency_amount(initial_equity, "initial equity", allow_zero=False)
    validate_currency_amount(base_rent, "monthly gross rent")
    validate_currency_amount(fixed_cost, "monthly fixed costs")
    if (
        isinstance(inputs.holding_months, bool)
        or not isinstance(inputs.holding_months, int)
        or inputs.holding_months <= 0
    ):
        raise ContractError("holding_months must be a positive integer")
    if inputs.loan_schedule and len(inputs.loan_schedule.payments) < inputs.holding_months:
        raise ContractError("loan schedule must cover the entire holding period")
    if inputs.loan_schedule and inputs.loan_schedule.as_of != as_of:
        raise ContractError("loan schedule and cash-flow as_of dates must match")
    financed_amount = (
        inputs.loan_schedule.principal_cny if inputs.loan_schedule else Decimal(0)
    )
    if initial_equity + financed_amount != purchase:
        raise ContractError("initial equity plus loan principal must equal purchase price")

    initial_outflow = -(initial_equity + acquisition)
    cumulative = initial_outflow
    minimum_cumulative = cumulative
    raw_cash_flows: list[Decimal] = [initial_outflow]
    rows: list[MonthlyCashFlow] = []
    yield_period_net_operating_income = Decimal(0)
    yield_period_months = min(inputs.holding_months, 12)
    ending_value = purchase

    for month in range(1, inputs.holding_months + 1):
        gross_rent = base_rent * ((Decimal(1) + rent_growth) ** (month - 1))
        effective_rent = gross_rent * occupancy
        operating_cost = fixed_cost + effective_rent * variable_cost_rate
        if month <= yield_period_months:
            yield_period_net_operating_income += effective_rent - operating_cost
        payment = (
            inputs.loan_schedule.payments[month - 1].payment_cny
            if inputs.loan_schedule
            else Decimal(0)
        )
        ending_value = purchase * ((Decimal(1) + property_growth) ** month)
        sale_proceeds = Decimal(0)
        if month == inputs.holding_months:
            loan_balance = (
                inputs.loan_schedule.payments[month - 1].remaining_principal_cny
                if inputs.loan_schedule
                else Decimal(0)
            )
            sale_proceeds = ending_value * (Decimal(1) - sale_cost_rate) - loan_balance
        net = effective_rent - operating_cost - payment + sale_proceeds
        cumulative += net
        minimum_cumulative = min(minimum_cumulative, cumulative)
        raw_cash_flows.append(net)
        rows.append(
            MonthlyCashFlow(
                month=month,
                gross_rent_cny=gross_rent,
                effective_rent_cny=effective_rent,
                operating_costs_cny=operating_cost,
                debt_service_cny=payment,
                sale_proceeds_cny=sale_proceeds,
                net_cash_flow_cny=net,
                cumulative_cash_flow_cny=cumulative,
            )
        )

    monthly_irr = _irr(raw_cash_flows)
    annual_irr = (
        (Decimal(1) + monthly_irr) ** 12 - Decimal(1)
        if monthly_irr is not None
        else None
    )
    npv = sum(
        value / ((Decimal(1) + discount_rate) ** month)
        for month, value in enumerate(raw_cash_flows)
    )
    loan_balance = (
        inputs.loan_schedule.payments[inputs.holding_months - 1].remaining_principal_cny
        if inputs.loan_schedule
        else Decimal(0)
    )
    input_references = list(readiness.input_evidence)
    input_references.extend(evidence_reference(item) for item in all_numeric_evidence)
    if inputs.loan_schedule:
        input_references.extend(inputs.loan_schedule.input_evidence)
    evidence_ids = [item.evidence_id for item in input_references]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ContractError("cash-flow evidence IDs must be unique")
    return ScenarioResult(
        scenario=scenario.name,
        monthly_cash_flows=tuple(rows),
        net_rental_yield=(
            yield_period_net_operating_income
            / Decimal(yield_period_months)
            * Decimal(12)
            / (purchase + acquisition)
        ),
        monthly_irr=monthly_irr,
        annualized_irr=annual_irr,
        npv_cny=npv,
        maximum_cash_shortfall_cny=max(Decimal(0), -minimum_cumulative),
        ending_property_value_cny=ending_value,
        ending_loan_balance_cny=loan_balance,
        input_evidence=tuple(input_references),
    )


def analyze_standard_scenarios(
    inputs: CashFlowInputs,
    scenarios: tuple[ScenarioAssumptions, ...],
    *,
    readiness: ReadinessResult,
    as_of: date,
) -> tuple[ScenarioResult, ...]:
    """Require and analyze exactly the conservative/base/optimistic set."""

    if not isinstance(scenarios, tuple) or any(
        not isinstance(scenario, ScenarioAssumptions) for scenario in scenarios
    ):
        raise ContractError("scenarios must be a tuple of ScenarioAssumptions")
    if any(
        not isinstance(scenario.name, str) or not scenario.name.strip()
        for scenario in scenarios
    ):
        raise ContractError("every scenario name must be a non-empty string")
    expected = {"conservative", "base", "optimistic"}
    names = {scenario.name for scenario in scenarios}
    if len(scenarios) != 3 or names != expected:
        raise ContractError(
            "scenarios must contain conservative, base, and optimistic exactly once"
        )
    results = tuple(
        analyze_scenario(inputs, scenario, readiness=readiness, as_of=as_of)
        for scenario in scenarios
    )
    references_by_id: dict[str, EvidenceReference] = {}
    for result in results:
        for reference in result.input_evidence:
            existing = references_by_id.setdefault(reference.evidence_id, reference)
            if existing != reference:
                raise ContractError(
                    "one evidence ID maps to conflicting scenario references"
                )
    return results
