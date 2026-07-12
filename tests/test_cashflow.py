from __future__ import annotations

import unittest
from dataclasses import replace
from datetime import date
from decimal import Decimal

from core.cashflow import (
    CashFlowInputs,
    ScenarioAssumptions,
    analyze_scenario,
    analyze_standard_scenarios,
)
from core.contracts import (
    ContractError,
    EvidenceKind,
    EvidenceNotUsableError,
    EvidenceRole,
    EvidenceStatus,
    Unit,
)
from core.loan import RepaymentMethod, build_loan_schedule
from core.readiness import evaluate_buy_readiness
from core.readiness import CheckName, CheckOutcome
from tests.test_readiness import clear_checks
from tests.helpers import categorical, numeric


def scenario(
    name: str,
    rent_growth: str = "0",
    property_growth: str = "0",
    occupancy: str = "1",
    sale_cost: str = "0",
    discount: str = "0",
) -> ScenarioAssumptions:
    return ScenarioAssumptions(
        name=name,
        monthly_rent_growth_rate=numeric(
            f"{name}-rent-growth",
            rent_growth,
            Unit.RATIO_PER_MONTH,
            kind=EvidenceKind.SCENARIO_ASSUMPTION,
            role=EvidenceRole.MONTHLY_RENT_GROWTH_RATE,
        ),
        monthly_property_growth_rate=numeric(
            f"{name}-price-growth",
            property_growth,
            Unit.RATIO_PER_MONTH,
            kind=EvidenceKind.SCENARIO_ASSUMPTION,
            role=EvidenceRole.MONTHLY_PROPERTY_GROWTH_RATE,
        ),
        occupancy_rate=numeric(
            f"{name}-occupancy",
            occupancy,
            Unit.RATIO,
            kind=EvidenceKind.SCENARIO_ASSUMPTION,
            role=EvidenceRole.OCCUPANCY_RATE,
        ),
        sale_cost_rate=numeric(
            f"{name}-sale-cost",
            sale_cost,
            Unit.RATIO,
            kind=EvidenceKind.SCENARIO_ASSUMPTION,
            role=EvidenceRole.SALE_COST_RATE,
        ),
        monthly_discount_rate=numeric(
            f"{name}-discount",
            discount,
            Unit.RATIO_PER_MONTH,
            kind=EvidenceKind.SCENARIO_ASSUMPTION,
            role=EvidenceRole.MONTHLY_DISCOUNT_RATE,
        ),
    )


def inputs(holding_months: int = 12, with_loan: bool = False) -> CashFlowInputs:
    loan = None
    if with_loan:
        loan = build_loan_schedule(
            principal=numeric(
                "loan-principal",
                "600000",
                Unit.CNY,
                role=EvidenceRole.LOAN_PRINCIPAL,
            ),
            annual_rate=numeric(
                "bank-quote",
                "0.036",
                Unit.RATIO_PER_YEAR,
                kind=EvidenceKind.BANK_MORTGAGE_EXECUTION_QUOTE,
                role=EvidenceRole.BANK_MORTGAGE_EXECUTION_RATE,
                borrower_id="BORROWER-TEST-001",
            ),
            months=holding_months,
            method=RepaymentMethod.EQUAL_PAYMENT,
            as_of=date(2026, 7, 12),
        )
    return CashFlowInputs(
        purchase_price=numeric(
            "purchase", "1000000", Unit.CNY, role=EvidenceRole.PURCHASE_PRICE
        ),
        acquisition_costs=numeric(
            "acquisition", "20000", Unit.CNY, role=EvidenceRole.ACQUISITION_COSTS
        ),
        initial_equity=numeric(
            "equity",
            "400000" if with_loan else "1000000",
            Unit.CNY,
            role=EvidenceRole.INITIAL_EQUITY,
        ),
        monthly_gross_rent=numeric(
            "rent",
            "3000",
            Unit.CNY_PER_MONTH,
            role=EvidenceRole.MONTHLY_GROSS_RENT,
        ),
        monthly_fixed_costs=numeric(
            "fixed-cost",
            "200",
            Unit.CNY_PER_MONTH,
            role=EvidenceRole.MONTHLY_FIXED_COSTS,
        ),
        variable_operating_cost_rate=numeric(
            "variable-cost",
            "0.1",
            Unit.RATIO,
            kind=EvidenceKind.SCENARIO_ASSUMPTION,
            role=EvidenceRole.VARIABLE_OPERATING_COST_RATE,
        ),
        holding_months=holding_months,
        loan_schedule=loan,
    )


class CashFlowTests(unittest.TestCase):
    AS_OF = date(2026, 7, 12)

    def readiness(self):
        return evaluate_buy_readiness(clear_checks(), as_of=self.AS_OF)

    def test_monthly_cashflow_and_metrics_without_loan(self) -> None:
        result = analyze_scenario(
            inputs(), scenario("base"), readiness=self.readiness(), as_of=self.AS_OF
        )
        self.assertEqual(12, len(result.monthly_cash_flows))
        self.assertEqual("2500.0", str(result.monthly_cash_flows[0].net_cash_flow_cny))
        self.assertEqual(
            "1002500.0", str(result.monthly_cash_flows[-1].net_cash_flow_cny)
        )
        self.assertEqual(
            "0.02941176470588235294117647059", str(result.net_rental_yield)
        )
        self.assertEqual("10000.0", str(result.npv_cny))
        self.assertEqual("1020000", str(result.maximum_cash_shortfall_cny))
        self.assertIsNotNone(result.annualized_irr)
        self.assertEqual(18, len(result.input_evidence))

    def test_loan_debt_service_and_sale_payoff_are_included(self) -> None:
        result = analyze_scenario(
            inputs(with_loan=True),
            scenario("base"),
            readiness=self.readiness(),
            as_of=self.AS_OF,
        )
        self.assertGreater(result.monthly_cash_flows[0].debt_service_cny, 0)
        self.assertEqual("0.00", str(result.ending_loan_balance_cny))
        self.assertGreater(result.monthly_cash_flows[-1].sale_proceeds_cny, 0)
        self.assertEqual(20, len(result.input_evidence))

    def test_price_and_rent_growth_apply_month_by_month(self) -> None:
        result = analyze_scenario(
            inputs(holding_months=2),
            scenario("base", rent_growth="0.01", property_growth="0.01"),
            readiness=self.readiness(),
            as_of=self.AS_OF,
        )
        self.assertEqual("3030.00", str(result.monthly_cash_flows[1].gross_rent_cny))
        self.assertEqual("1020100.0000", str(result.ending_property_value_cny))

    def test_net_rental_yield_uses_the_actual_yield_period(self) -> None:
        result = analyze_scenario(
            inputs(),
            scenario("base", rent_growth="0.10"),
            readiness=self.readiness(),
            as_of=self.AS_OF,
        )
        monthly_noi = [
            row.effective_rent_cny - row.operating_costs_cny
            for row in result.monthly_cash_flows[:12]
        ]
        expected = sum(monthly_noi) / Decimal(12) * Decimal(12) / Decimal(1020000)
        self.assertEqual(expected, result.net_rental_yield)

    def test_standard_scenario_set_is_required(self) -> None:
        valid = (
            scenario("conservative", property_growth="-0.005"),
            scenario("base"),
            scenario("optimistic", property_growth="0.005"),
        )
        results = analyze_standard_scenarios(
            inputs(), valid, readiness=self.readiness(), as_of=self.AS_OF
        )
        self.assertEqual(
            ["conservative", "base", "optimistic"],
            [result.scenario for result in results],
        )
        with self.assertRaisesRegex(ContractError, "conservative"):
            analyze_standard_scenarios(
                inputs(),
                (scenario("base"),),
                readiness=self.readiness(),
                as_of=self.AS_OF,
            )

    def test_unverified_assumption_is_refused(self) -> None:
        bad = scenario("base")
        bad = ScenarioAssumptions(
            name=bad.name,
            monthly_rent_growth_rate=numeric(
                "unverified-growth",
                "0.01",
                Unit.RATIO_PER_MONTH,
                EvidenceStatus.UNVERIFIED,
                EvidenceKind.SCENARIO_ASSUMPTION,
                EvidenceRole.MONTHLY_RENT_GROWTH_RATE,
            ),
            monthly_property_growth_rate=bad.monthly_property_growth_rate,
            occupancy_rate=bad.occupancy_rate,
            sale_cost_rate=bad.sale_cost_rate,
            monthly_discount_rate=bad.monthly_discount_rate,
        )
        with self.assertRaises(EvidenceNotUsableError):
            analyze_scenario(
                inputs(), bad, readiness=self.readiness(), as_of=self.AS_OF
            )

    def test_invalid_occupancy_and_growth_are_refused(self) -> None:
        with self.assertRaises(ContractError):
            analyze_scenario(
                inputs(),
                scenario("base", occupancy="1.01"),
                readiness=self.readiness(),
                as_of=self.AS_OF,
            )

    def test_verified_evidence_roles_cannot_be_swapped(self) -> None:
        base = inputs()
        swapped_inputs = CashFlowInputs(
            purchase_price=base.purchase_price,
            acquisition_costs=base.acquisition_costs,
            initial_equity=base.initial_equity,
            monthly_gross_rent=base.monthly_fixed_costs,
            monthly_fixed_costs=base.monthly_gross_rent,
            variable_operating_cost_rate=base.variable_operating_cost_rate,
            holding_months=base.holding_months,
        )
        with self.assertRaisesRegex(EvidenceNotUsableError, "role"):
            analyze_scenario(
                swapped_inputs,
                scenario("base"),
                readiness=self.readiness(),
                as_of=self.AS_OF,
            )

        base_scenario = scenario("base")
        swapped_scenario = ScenarioAssumptions(
            name="base",
            monthly_rent_growth_rate=base_scenario.monthly_rent_growth_rate,
            monthly_property_growth_rate=base_scenario.monthly_property_growth_rate,
            occupancy_rate=base_scenario.sale_cost_rate,
            sale_cost_rate=base_scenario.occupancy_rate,
            monthly_discount_rate=base_scenario.monthly_discount_rate,
        )
        with self.assertRaisesRegex(EvidenceNotUsableError, "role"):
            analyze_scenario(
                base,
                swapped_scenario,
                readiness=self.readiness(),
                as_of=self.AS_OF,
            )

    def test_invalid_scenario_name_raises_contract_error(self) -> None:
        with self.assertRaisesRegex(ContractError, "scenario name"):
            analyze_scenario(
                inputs(),
                replace(scenario("base"), name=None),  # type: ignore[arg-type]
                readiness=self.readiness(),
                as_of=self.AS_OF,
            )

    def test_duplicate_evidence_id_across_slots_is_refused(self) -> None:
        base = inputs()
        duplicate_id = CashFlowInputs(
            purchase_price=base.purchase_price,
            acquisition_costs=numeric(
                base.purchase_price.metadata.evidence_id,
                "20000",
                Unit.CNY,
                role=EvidenceRole.ACQUISITION_COSTS,
            ),
            initial_equity=base.initial_equity,
            monthly_gross_rent=base.monthly_gross_rent,
            monthly_fixed_costs=base.monthly_fixed_costs,
            variable_operating_cost_rate=base.variable_operating_cost_rate,
            holding_months=base.holding_months,
        )
        with self.assertRaisesRegex(ContractError, "IDs must be unique"):
            analyze_scenario(
                duplicate_id,
                scenario("base"),
                readiness=self.readiness(),
                as_of=self.AS_OF,
            )

    def test_duplicate_id_between_readiness_and_numeric_input_is_refused(self) -> None:
        base = inputs()
        collided = CashFlowInputs(
            purchase_price=numeric(
                CheckName.TITLE.value,
                "1000000",
                Unit.CNY,
                role=EvidenceRole.PURCHASE_PRICE,
            ),
            acquisition_costs=base.acquisition_costs,
            initial_equity=base.initial_equity,
            monthly_gross_rent=base.monthly_gross_rent,
            monthly_fixed_costs=base.monthly_fixed_costs,
            variable_operating_cost_rate=base.variable_operating_cost_rate,
            holding_months=base.holding_months,
        )
        with self.assertRaisesRegex(ContractError, "IDs must be unique"):
            analyze_scenario(
                collided,
                scenario("base"),
                readiness=self.readiness(),
                as_of=self.AS_OF,
            )

    def test_standard_scenario_invalid_name_is_contract_error(self) -> None:
        scenarios = (
            replace(scenario("conservative"), name=[]),  # type: ignore[arg-type]
            scenario("base"),
            scenario("optimistic"),
        )
        with self.assertRaisesRegex(ContractError, "scenario name"):
            analyze_standard_scenarios(
                inputs(), scenarios, readiness=self.readiness(), as_of=self.AS_OF
            )

    def test_standard_scenarios_reject_conflicting_shared_evidence_id(self) -> None:
        conservative = scenario("conservative", rent_growth="-0.01")
        base = scenario("base")
        optimistic = scenario("optimistic", rent_growth="0.01")
        scenarios = tuple(
            replace(
                item,
                monthly_rent_growth_rate=numeric(
                    "shared-rent-growth",
                    str(item.monthly_rent_growth_rate.value),
                    Unit.RATIO_PER_MONTH,
                    kind=EvidenceKind.SCENARIO_ASSUMPTION,
                    role=EvidenceRole.MONTHLY_RENT_GROWTH_RATE,
                ),
            )
            for item in (conservative, base, optimistic)
        )
        with self.assertRaisesRegex(ContractError, "conflicting scenario"):
            analyze_standard_scenarios(
                inputs(), scenarios, readiness=self.readiness(), as_of=self.AS_OF
            )
        with self.assertRaises(ContractError):
            analyze_scenario(
                inputs(),
                scenario("base", property_growth="-1"),
                readiness=self.readiness(),
                as_of=self.AS_OF,
            )

    def test_short_loan_schedule_is_refused(self) -> None:
        base = inputs(holding_months=12)
        short_loan = build_loan_schedule(
            principal=numeric(
                "loan", "100000", Unit.CNY, role=EvidenceRole.LOAN_PRINCIPAL
            ),
            annual_rate=numeric(
                "rate",
                "0.03",
                Unit.RATIO_PER_YEAR,
                kind=EvidenceKind.BANK_MORTGAGE_EXECUTION_QUOTE,
                role=EvidenceRole.BANK_MORTGAGE_EXECUTION_RATE,
                borrower_id="BORROWER-TEST-001",
            ),
            months=6,
            method=RepaymentMethod.EQUAL_PAYMENT,
            as_of=self.AS_OF,
        )
        invalid = CashFlowInputs(
            purchase_price=base.purchase_price,
            acquisition_costs=base.acquisition_costs,
            initial_equity=base.initial_equity,
            monthly_gross_rent=base.monthly_gross_rent,
            monthly_fixed_costs=base.monthly_fixed_costs,
            variable_operating_cost_rate=base.variable_operating_cost_rate,
            holding_months=12,
            loan_schedule=short_loan,
        )
        with self.assertRaisesRegex(ContractError, "entire holding period"):
            analyze_scenario(
                invalid,
                scenario("base"),
                readiness=self.readiness(),
                as_of=self.AS_OF,
            )

    def test_unreconciled_financing_is_refused(self) -> None:
        base = inputs(with_loan=True)
        invalid = CashFlowInputs(
            purchase_price=base.purchase_price,
            acquisition_costs=base.acquisition_costs,
            initial_equity=numeric(
                "wrong-equity",
                "399999",
                Unit.CNY,
                role=EvidenceRole.INITIAL_EQUITY,
            ),
            monthly_gross_rent=base.monthly_gross_rent,
            monthly_fixed_costs=base.monthly_fixed_costs,
            variable_operating_cost_rate=base.variable_operating_cost_rate,
            holding_months=base.holding_months,
            loan_schedule=base.loan_schedule,
        )
        with self.assertRaisesRegex(ContractError, "must equal purchase price"):
            analyze_scenario(
                invalid,
                scenario("base"),
                readiness=self.readiness(),
                as_of=self.AS_OF,
            )

    def test_closed_readiness_gate_blocks_cashflow(self) -> None:
        checks = clear_checks()
        checks.pop(next(iter(checks)))
        closed = evaluate_buy_readiness(checks, as_of=self.AS_OF)
        with self.assertRaisesRegex(ContractError, "readiness gate"):
            analyze_scenario(
                inputs(), scenario("base"), readiness=closed, as_of=self.AS_OF
            )

    def test_tampered_readiness_result_is_rejected(self) -> None:
        with self.assertRaisesRegex(ContractError, "open readiness"):
            replace(self.readiness(), passed_checks=())

    def test_adverse_readiness_cannot_be_forged_open(self) -> None:
        checks = clear_checks()
        checks[CheckName.TITLE] = categorical(
            CheckName.TITLE.value, CheckOutcome.ADVERSE
        )
        closed = evaluate_buy_readiness(checks, as_of=self.AS_OF)
        with self.assertRaisesRegex(ContractError, "unusable evidence"):
            replace(
                closed,
                analysis_ready=True,
                decision="ANALYSIS_READY",
                blockers=(),
                passed_checks=tuple(CheckName),
            )

    def test_cross_property_evidence_is_refused(self) -> None:
        base = inputs()
        mismatched = CashFlowInputs(
            purchase_price=numeric(
                "other-property-price",
                "1000000",
                Unit.CNY,
                role=EvidenceRole.PURCHASE_PRICE,
                property_id="PROPERTY-OTHER",
            ),
            acquisition_costs=base.acquisition_costs,
            initial_equity=base.initial_equity,
            monthly_gross_rent=base.monthly_gross_rent,
            monthly_fixed_costs=base.monthly_fixed_costs,
            variable_operating_cost_rate=base.variable_operating_cost_rate,
            holding_months=base.holding_months,
        )
        with self.assertRaisesRegex(ContractError, "one case, property, and borrower"):
            analyze_scenario(
                mismatched,
                scenario("base"),
                readiness=self.readiness(),
                as_of=self.AS_OF,
            )

    def test_cross_borrower_evidence_is_refused_end_to_end(self) -> None:
        base = inputs(with_loan=True)
        mismatched = CashFlowInputs(
            purchase_price=base.purchase_price,
            acquisition_costs=base.acquisition_costs,
            initial_equity=numeric(
                "other-borrower-equity",
                "400000",
                Unit.CNY,
                role=EvidenceRole.INITIAL_EQUITY,
                borrower_id="BORROWER-OTHER",
            ),
            monthly_gross_rent=base.monthly_gross_rent,
            monthly_fixed_costs=base.monthly_fixed_costs,
            variable_operating_cost_rate=base.variable_operating_cost_rate,
            holding_months=base.holding_months,
            loan_schedule=base.loan_schedule,
        )
        with self.assertRaisesRegex(ContractError, "property, and borrower"):
            analyze_scenario(
                mismatched,
                scenario("base"),
                readiness=self.readiness(),
                as_of=self.AS_OF,
            )


if __name__ == "__main__":
    unittest.main()
