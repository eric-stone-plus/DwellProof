#!/usr/bin/env python3
"""Regression tests for the retired housing-prototype safety boundary."""

from __future__ import annotations

import json
import sys
import subprocess
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock

import numpy as np
import pandas as pd


OUTPUT = Path(__file__).resolve().parent
if str(OUTPUT) not in sys.path:
    sys.path.insert(0, str(OUTPUT))

from analysis_utils import best_lag_correlation
from auto_update import SAFE_UPDATE_STEPS, main as auto_update_main
from fetch_cities import CITIES, TARGET, atomic_write_csv, validate_dataset
from fetch_more_cities import (
    EXTRA_CITIES,
    build_expanded,
    validate_fetched_batch,
    validate_publication_boundary,
)
from legacy_alert import AlertEngine
from legacy_backtest import BacktestEngine
from legacy_decision import DecisionEngine
from legacy_main import LegacyMarketContext
from legacy_mcp import LegacyMarketContextMCP
from legacy_uha import UnifiedHousingAccount
from legacy_valuation import PropertyValuator, render_refusal_report
from mega_analysis import load_all
from monitoring import (
    MONITOR_CITIES,
    generate_monitoring_report,
    publish_latest_data,
    validate_monitoring_dataset,
)


PRICE_COLUMNS = [
    "新建商品住宅价格指数-同比",
    "新建商品住宅价格指数-环比",
    "二手住宅价格指数-同比",
    "二手住宅价格指数-环比",
]


def make_city_frame(cities, date="2026-04-01", *, include_tier=False):
    rows = []
    tiers = {
        city: tier
        for tier, tier_cities in MONITOR_CITIES.items()
        for city in tier_cities
    }
    for city in cities:
        row = {"城市": city, "日期": date}
        row.update({column: 100.0 for column in PRICE_COLUMNS})
        if include_tier:
            row["梯队"] = tiers[city]
        rows.append(row)
    return pd.DataFrame(rows)


class PathAndDataTests(unittest.TestCase):
    def test_runtime_root_is_current_directory(self):
        self.assertEqual(OUTPUT, Path(__file__).resolve().parent)
        self.assertEqual(TARGET, OUTPUT / "70city_full.csv")

    def test_required_data_and_reports_exist(self):
        files = [
            "70city_full.csv", "70city_expanded.csv", "construction_index.csv",
            "gdp.csv", "cpi.csv", "pmi.csv", "lpr.csv", "m2.csv",
            "QUICK_REFERENCE.md", "ARCHITECTURE.md", "UNIFIED_STANDARDS.md",
        ]
        for filename in files:
            with self.subTest(filename=filename):
                path = OUTPUT / filename
                self.assertTrue(path.is_file(), filename)
                self.assertGreater(path.stat().st_size, 100, filename)

    def test_pmi_latest_observation_is_not_last_file_row(self):
        pmi = pd.read_csv(OUTPUT / "pmi.csv")
        latest = pmi.sort_values("月份").iloc[-1]
        self.assertEqual(latest["月份"], "2026年05月份")
        self.assertEqual(float(latest["制造业-指数"]), 50.0)
        self.assertEqual(float(latest["非制造业-指数"]), 50.1)


class DecisionSafetyTests(unittest.TestCase):
    def setUp(self):
        self.market_only = {
            "mom": 100.7, "yoy": 94.4, "regime": "R3",
            "trend": 0.5, "season": 3,
        }

    def test_city_index_never_produces_actionable_decision(self):
        result = DecisionEngine().analyze("上海", self.market_only)
        self.assertEqual(result["decision_status"], "insufficient_evidence")
        self.assertTrue(result["missing_evidence"])
        for action in ("buy", "sell", "hold"):
            self.assertFalse(result["signals"][action]["actionable"])
            self.assertIn("证据不足", result["signals"][action]["signal"])

    def test_mcp_deprecated_directional_aliases_fail_closed(self):
        mcp = LegacyMarketContextMCP()
        results = (
            mcp.get_buy_signal("上海"),
            mcp.get_sell_signal("上海"),
            mcp.get_leading_indicator(),
            mcp.get_seasonal_pattern("广州"),
            mcp.get_investment_ranking(),
        )
        for result in results:
            self.assertEqual(result["status"], "INSUFFICIENT_EVIDENCE")
            self.assertTrue(result["deprecated"])
            self.assertFalse(result["actionable"])
        self.assertEqual(results[-1]["ranking"], [])
        self.assertNotIn("best_month", results[3])
        self.assertNotIn("lead_time", results[2])

    def test_mcp_registry_and_safe_outputs_use_market_context_semantics(self):
        mcp = LegacyMarketContextMCP()
        descriptions = "\n".join(
            tool["description"] for tool in mcp.list_tools()
        )
        for forbidden in (
            "买房信号", "卖房信号", "全国领先", "最佳卖月", "投资排名",
        ):
            self.assertNotIn(forbidden, descriptions)

        city = mcp.get_city_data("上海")
        snapshot = mcp.get_market_snapshot()
        shanghai = mcp.get_shanghai_observation()
        seasonal = mcp.get_seasonality_context("广州")
        for result in (city, snapshot, shanghai, seasonal):
            self.assertFalse(result["actionable"])
        self.assertEqual(city["status"], "MARKET_CONTEXT_ONLY")
        self.assertEqual(snapshot["coverage"], "legacy_configured_city_set")
        self.assertIn("不得外推", shanghai["note"])
        self.assertIn("不代表未来走势", seasonal["note"])
        self.assertNotIn("best_month", seasonal)

    def test_alerts_are_non_actionable_manual_review_prompts(self):
        alerts = AlertEngine().check_all_cities({
            "上海": {"mom": 100.7, "yoy": 94.4},
            "测试城": {"mom": 98.8, "yoy": 89.0},
            "_national": {"index": 89.0},
            "_macro": {"lpr_change": -0.1},
        })
        self.assertTrue(alerts)
        rendered = AlertEngine().format_alerts(alerts)
        self.assertIn("人工核验", rendered)
        self.assertNotIn("全国2-5月后跟涨", rendered)
        self.assertNotIn("最佳卖房时机", rendered)
        for alert in alerts:
            payload = alert.to_dict()
            self.assertEqual(payload["status"], "INSUFFICIENT_EVIDENCE")
            self.assertFalse(payload["actionable"])
            self.assertEqual(payload["role"], "market_context_review")

    def test_legacy_directional_backtests_are_disabled(self):
        engine = BacktestEngine()
        for result in (
            engine.backtest_buy_signal(pd.DataFrame(), "上海"),
            engine.backtest_sell_signal(pd.DataFrame(), "上海"),
        ):
            self.assertEqual(result["status"], "disabled")
            self.assertFalse(result["actionable"])
            self.assertNotIn("accuracy", result)

        leading = engine.backtest_leading_indicator(pd.DataFrame())
        self.assertEqual(leading["status"], "disabled")
        self.assertFalse(leading["actionable"])
        self.assertEqual(leading["results"], {})
        self.assertNotIn("accuracy", leading)

    def test_unsafe_legacy_generators_refuse_direct_execution(self):
        for script, marker in (
            ("housing_model.py", "DISABLED_LEGACY_MODEL"),
            ("cycle_prediction.py", "DISABLED_LEGACY_FORECAST"),
            ("history_cycle_invest.py", "DISABLED_LEGACY_REPORT"),
            ("credit_analysis.py", "DISABLED_LEGACY_CREDIT_ANALYSIS"),
            ("legacy_risk.py", "DISABLED_LEGACY_RISK_SCORE"),
            ("gz_sell_guide.py", "DISABLED_LEGACY_SELL_GUIDE"),
            ("batch_sell_guides.py", "DISABLED_LEGACY_BATCH_SELL_GUIDES"),
            ("macro_analysis.py", "DISABLED_LEGACY_MACRO_ANALYSIS"),
            ("cycle_features.py", "DISABLED_LEGACY_CYCLE_FEATURES"),
            ("full_city_ranking.py", "DISABLED_LEGACY_CITY_RANKING"),
            ("full_analysis.py", "DISABLED_LEGACY_FULL_ANALYSIS"),
            ("data_analysis.py", "DISABLED_LEGACY_DATA_ANALYSIS"),
            ("market_timing.py", "DISABLED_LEGACY_MARKET_TIMING"),
            ("city_transmission.py", "DISABLED_LEGACY_CITY_TRANSMISSION"),
            ("mega_analysis.py", "DISABLED_LEGACY_MEGA_REPORT"),
            ("legacy_uha.py", "DISABLED_LEGACY_UHA_DEMO"),
            ("legacy_alert.py", "DISABLED_LEGACY_ALERT_DEMO"),
        ):
            with self.subTest(script=script):
                result = subprocess.run(
                    [sys.executable, str(OUTPUT / script)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(marker, result.stderr + result.stdout)

    def test_monitoring_report_has_no_heuristic_decision_labels(self):
        frame = make_city_frame(
            [city for cities in MONITOR_CITIES.values() for city in cities],
            include_tier=True,
        )
        report = generate_monitoring_report(frame)
        self.assertIn("仅作市场背景", report)
        for forbidden in (
            "Regime", "预警信号", "领先指标", "旧假设滞后参数", "交易建议",
        ):
            if forbidden == "交易建议":
                self.assertIn("不生成预警、周期标签、跨城预测或交易建议", report)
            else:
                self.assertNotIn(forbidden, report)

    def test_legacy_calculator_only_generates_a_refusal(self):
        source = (OUTPUT / "calculator_tools.py").read_text(encoding="utf-8")
        self.assertIn("INSUFFICIENT_EVIDENCE", source)
        for unsafe_default in ("3.5 / 100", "0.053", "0.015", "已还5年"):
            self.assertNotIn(unsafe_default, source)

    def test_every_legacy_static_report_has_a_front_matter_warning(self):
        required = (
            "LEGACY_ARCHIVE_UNVERIFIED",
            "INSUFFICIENT_EVIDENCE",
            "actionable: false",
            "原 HouseAlice",
            "不属于 DwellProof",
            "不得用于",
        )
        for path in OUTPUT.glob("*.md"):
            with self.subTest(path=path.name):
                front_matter = "\n".join(
                    line
                    for line in path.read_text(
                        encoding="utf-8", errors="replace"
                    ).splitlines()
                    if line.strip()
                )[:2000]
                for marker in required:
                    self.assertIn(marker, front_matter, path.name)

        for path in OUTPUT.glob("*.html"):
            with self.subTest(path=path.name):
                document = path.read_text(encoding="utf-8", errors="replace")
                body = document.split("<body", 1)[1][:2000]
                self.assertIn('class="archive-warning" role="alert"', body)
                for marker in required:
                    self.assertIn(marker, body, path.name)


class ModelAndMergeTests(unittest.TestCase):
    def test_unknown_valuation_inputs_are_rejected(self):
        valuator = PropertyValuator()
        unknown_city = valuator.estimate("不存在城市", "未知区", 80)
        unknown_district = valuator.estimate("广州", "未知区", 80)
        self.assertIn("error", unknown_city)
        self.assertIn("error", unknown_district)
        self.assertFalse(unknown_city["actionable"])
        self.assertFalse(unknown_district["actionable"])

    def test_known_valuation_fails_closed_without_comparables(self):
        result = PropertyValuator().estimate("广州", "天河", 89)
        self.assertEqual(result["status"], "INSUFFICIENT_PROPERTY_EVIDENCE")
        self.assertFalse(result["actionable"])
        self.assertFalse(result["valuation_available"])
        for forbidden in (
            "base_price", "unit_price", "total_price", "district_factor",
            "floor_factor", "orientation_factor", "decoration_factor",
        ):
            self.assertNotIn(forbidden, result)

    def test_valuation_report_preserves_refusal_without_prices(self):
        results = PropertyValuator().batch_estimate([
            {
                "city": "广州", "district": "天河", "area": 89,
                "floor": 25, "orientation": "南", "decoration": "精装",
            },
        ])
        self.assertEqual(
            results[0]["status"], "INSUFFICIENT_PROPERTY_EVIDENCE"
        )
        self.assertNotIn("total_price", results[0])
        report = render_refusal_report(results)
        self.assertIn("INSUFFICIENT_PROPERTY_EVIDENCE", report)
        self.assertIn("不可操作", report)
        self.assertIn("未计算", report)
        self.assertNotIn("单价(万/㎡)", report)
        self.assertNotIn("总价(万)", report)

    def test_mega_merge_has_unique_city_dates(self):
        combined = load_all()
        self.assertFalse(combined.duplicated(["城市", "日期"]).any())
        self.assertEqual(len(combined), 11592)
        self.assertEqual(combined["城市"].nunique(), 63)

    def test_expanded_merge_prefers_main_and_deduplicates(self):
        main = pd.DataFrame({
            "城市": ["上海"], "日期": ["2026-01-01"], "value": [1]
        })
        extra = pd.DataFrame({
            "城市": ["上海", "杭州"],
            "日期": ["2026-01-01", "2026-01-01"],
            "value": [999, 2],
        })
        for column in {
            "新建商品住宅价格指数-同比", "新建商品住宅价格指数-环比",
            "二手住宅价格指数-同比", "二手住宅价格指数-环比",
        }:
            main[column] = 100.0
            extra[column] = 100.0
        merged = build_expanded(main, [extra])
        self.assertEqual(len(merged), 2)
        shanghai = merged.loc[merged["城市"] == "上海"].iloc[0]
        self.assertEqual(shanghai["value"], 1)

    def test_best_lag_correlation_does_not_stick_at_negative_one(self):
        rng = np.random.default_rng(7)
        reference = rng.normal(size=100)
        target = np.roll(reference, 2)
        lag, corr = best_lag_correlation(reference, target, max_lag=4)
        self.assertNotEqual(corr, -1)
        self.assertGreater(abs(corr), 0.9)
        self.assertIn(lag, (-2, 2))


class UpdateAndAccountTests(unittest.TestCase):
    def test_default_update_paths_exclude_prediction_and_advice_generators(self):
        scripts = [script for script, _ in SAFE_UPDATE_STEPS]
        self.assertEqual(
            scripts,
            ["fetch_cities.py", "fetch_more_cities.py", "legacy_main.py"],
        )
        shell = (OUTPUT / "housing_monitor.sh").read_text(encoding="utf-8")
        for forbidden in (
            "mega_analysis.py", "cycle_prediction.py", "market_timing.py",
            "monitoring.py",
        ):
            self.assertNotIn(forbidden, shell)

    def test_auto_update_stops_at_first_failure(self):
        with mock.patch("auto_update.run_script", side_effect=[True, False]) as run:
            status = auto_update_main()
        self.assertEqual(status, 1)
        self.assertEqual(run.call_count, 2)

    def test_main_report_is_market_context_only_and_handles_unknown_values(self):
        account = UnifiedHousingAccount("test")
        account.add_property(
            city="广州", district="天河", address="test", buy_price=100,
            buy_date="2020-01-01", area=50,
        )
        with mock.patch(
            "legacy_main.UnifiedHousingAccount.load", return_value=account
        ):
            report = LegacyMarketContext("test").dashboard()

        self.assertIn("INSUFFICIENT_EVIDENCE", report)
        self.assertIn("PERSONAL_STATE_UNVERIFIED", report)
        self.assertIn("Configured-city index snapshot", report)
        self.assertNotIn("Recorded properties:", report)
        self.assertNotIn("Recorded acquisition cost:", report)
        for forbidden in (
            "买房信号", "卖房信号", "最佳月份", "投资排名", "领先时间",
        ):
            self.assertNotIn(forbidden, report)

    def test_uha_uses_local_default_path(self):
        loaded = UnifiedHousingAccount.load()
        self.assertIsInstance(loaded, UnifiedHousingAccount)

    def test_uha_city_index_is_context_and_never_changes_value(self):
        account = UnifiedHousingAccount("test")
        prop = account.add_property(
            city="广州", district="天河", address="test", buy_price=100,
            buy_date="2020-01-01", area=50,
        )
        first = account.update_values({"广州": 100.2}, "2026-04")

        self.assertEqual(
            first["status"], "INSUFFICIENT_PROPERTY_EVIDENCE"
        )
        self.assertFalse(first["actionable"])
        self.assertEqual(first["property_values_changed"], 0)
        self.assertEqual(first["market_context_recorded"], 1)
        self.assertIsNone(prop.current_value)
        self.assertIsNone(account.total_value())
        self.assertIsNone(prop.return_rate())
        self.assertIsNone(prop.rental_yield())
        self.assertEqual(
            prop.market_context["2026-04"]["index_value"], 100.2
        )
        self.assertEqual(
            prop.market_context["2026-04"]["role"], "market_context"
        )

    def test_uha_context_observation_is_idempotent_and_conflict_safe(self):
        account = UnifiedHousingAccount("test")
        prop = account.add_property(
            city="广州", district="天河", address="test", buy_price=100,
            buy_date="2020-01-01", area=50,
        )
        account.update_values({"广州": 100.2}, "2026-04")
        duplicate = account.update_values({"广州": 100.2}, "2026-04")
        conflict = account.update_values({"广州": 99.9}, "2026-04")

        self.assertEqual(duplicate["market_context_recorded"], 0)
        self.assertEqual(duplicate["duplicate_observations"], 1)
        self.assertEqual(duplicate["observation_conflicts"], 0)
        self.assertEqual(conflict["observation_conflicts"], 1)
        self.assertEqual(len(prop.market_context), 1)
        self.assertEqual(
            prop.market_context["2026-04"]["index_value"], 100.2
        )
        self.assertIsNone(prop.current_value)

    def test_uha_context_update_requires_observation_id(self):
        account = UnifiedHousingAccount("test")
        prop = account.add_property(
            city="广州", district="天河", address="test", buy_price=100,
            buy_date="2020-01-01", area=50,
        )
        with self.assertRaises(ValueError):
            account.update_values({"广州": 100.2})
        self.assertEqual(prop.market_context, {})
        self.assertIsNone(prop.current_value)

    def test_uha_update_property_value_alias_fails_closed(self):
        account = UnifiedHousingAccount("test")
        prop = account.add_property(
            city="广州", district="天河", address="test", buy_price=100,
            buy_date="2020-01-01", area=50,
        )
        result = prop.update_property_value(100.2, "2026-04")
        self.assertEqual(
            result["status"], "INSUFFICIENT_PROPERTY_EVIDENCE"
        )
        self.assertFalse(result["property_value_changed"])
        self.assertIsNone(prop.current_value)

    def test_uha_sale_records_gross_spread_but_not_profit(self):
        account = UnifiedHousingAccount("test")
        account.add_property(
            city="广州", district="天河", address="test", buy_price=100,
            buy_date="2020-01-01", area=50,
        )
        result = account.sell_property(0, 120)
        self.assertEqual(result["gross_price_spread"], 20)
        self.assertIsNone(result["profit"])
        self.assertIsNone(result["profit_rate"])
        self.assertFalse(result["actionable"])
        self.assertEqual(result["status"], "INSUFFICIENT_FULL_COST_EVIDENCE")

    def test_uha_sale_rejects_negative_index_and_invalid_price(self):
        account = UnifiedHousingAccount("test")
        account.add_property(
            city="广州", district="天河", address="test", buy_price=100,
            buy_date="2020-01-01", area=50,
        )
        self.assertIn("error", account.sell_property(-1, 120))
        self.assertIn("error", account.sell_property(0, float("nan")))
        self.assertEqual(len(account.properties), 1)

    def test_uha_summary_never_labels_cost_as_current_value_or_return(self):
        account = UnifiedHousingAccount("test")
        prop = account.add_property(
            city="广州", district="天河", address="test", buy_price=100,
            buy_date="2020-01-01", area=50,
        )
        prop.legacy_unverified_annual_rent = 3
        account.update_values({"广州": 100.2}, "2026-04")
        report = account.summary()

        self.assertIn("PERSONAL_STATE_UNVERIFIED", report)
        for forbidden in ("广州", "天河", "100万", "3.00%"):
            self.assertNotIn(forbidden, report)

    def test_uha_quarantines_unverified_legacy_rent(self):
        payload = {
            "name": "legacy-rent",
            "properties": [{
                "city": "广州", "district": "天河", "address": "test",
                "buy_price": 100, "buy_date": "2020-01-01", "area": 50,
                "annual_rent": 3,
            }],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "uha.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = UnifiedHousingAccount.load(path)

        prop = loaded.properties[0]
        self.assertIsNone(prop.annual_rent)
        self.assertEqual(prop.legacy_unverified_annual_rent, 3)
        self.assertIsNone(prop.rental_yield_on_cost())
        self.assertIsNone(loaded.total_rental_income())
        self.assertIsNone(loaded.total_rental_yield_on_cost())

    def test_uha_load_quarantines_legacy_derived_value(self):
        payload = {
            "name": "legacy",
            "properties": [{
                "city": "广州", "district": "天河", "address": "test",
                "buy_price": 100, "buy_date": "2020-01-01", "area": 50,
                "current_value": 92.1, "value_observation": "legacy-2026-04",
            }],
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "uha.json"
            path.write_text(
                json.dumps(payload, ensure_ascii=False),
                encoding="utf-8",
            )
            loaded = UnifiedHousingAccount.load(path)

        prop = loaded.properties[0]
        self.assertIsNone(prop.current_value)
        self.assertEqual(prop.legacy_unverified_value, 92.1)
        self.assertEqual(
            prop.value_status, "INSUFFICIENT_PROPERTY_EVIDENCE"
        )
        self.assertIsNone(loaded.total_value())
        self.assertIn("PERSONAL_STATE_UNVERIFIED", loaded.summary())

    def test_fetch_validation_rejects_incomplete_refresh(self):
        frame = pd.DataFrame({"城市": ["上海"], "日期": ["2026-01-01"]})
        with self.assertRaises(ValueError):
            validate_dataset(frame)


class PublicationGateTests(unittest.TestCase):
    def test_main_fetch_accepts_complete_contemporaneous_cross_section(self):
        validated = validate_dataset(make_city_frame(CITIES))
        self.assertEqual(set(validated["城市"]), set(CITIES))
        self.assertEqual(validated["日期"].nunique(), 1)

    def test_main_fetch_rejects_wrong_city_even_when_count_matches(self):
        cities = [*CITIES[:-1], "虚构城市"]
        with self.assertRaisesRegex(ValueError, "城市覆盖不完整"):
            validate_dataset(make_city_frame(cities))

    def test_main_fetch_rejects_city_lagging_global_latest_period(self):
        frame = make_city_frame(CITIES)
        frame.loc[frame["城市"] == CITIES[-1], "日期"] = "2026-03-01"
        with self.assertRaisesRegex(ValueError, "最新观察期不一致"):
            validate_dataset(frame)

    def test_main_fetch_rejects_duplicate_city_date(self):
        frame = make_city_frame(CITIES)
        frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, "重复的城市-日期"):
            validate_dataset(frame)

    def test_main_fetch_rejects_blank_latest_key_value(self):
        frame = make_city_frame(CITIES)
        frame.loc[frame["城市"] == "上海", PRICE_COLUMNS[0]] = None
        with self.assertRaisesRegex(ValueError, "最新期关键字段为空"):
            validate_dataset(frame)

    def test_extra_batch_requires_all_cities_and_same_latest_period(self):
        frames = {
            city: make_city_frame([city]) for city in EXTRA_CITIES
        }
        frames[EXTRA_CITIES[-1]].loc[:, "日期"] = "2026-03-01"
        with self.assertRaisesRegex(ValueError, "最新观察期不一致"):
            validate_fetched_batch(frames)

        del frames[EXTRA_CITIES[-1]]
        with self.assertRaisesRegex(ValueError, "城市覆盖不完整"):
            validate_fetched_batch(frames)

    def test_extra_batch_rejects_blank_latest_key_value(self):
        frames = {
            city: make_city_frame([city]) for city in EXTRA_CITIES
        }
        frames["佛山"].loc[:, PRICE_COLUMNS[-1]] = np.nan
        with self.assertRaisesRegex(ValueError, "关键价格指数为空"):
            validate_fetched_batch(frames)

    def test_extra_publication_requires_main_and_fetched_same_period(self):
        main = make_city_frame(CITIES, "2026-04-01")
        fetched = {
            city: make_city_frame([city], "2026-05-01")
            for city in EXTRA_CITIES
        }
        with self.assertRaisesRegex(ValueError, "主数据与当次扩展抓取"):
            validate_publication_boundary(main, fetched)

    def test_expanded_merge_allows_retained_city_to_be_historical(self):
        main = make_city_frame(["上海"], "2026-04-01")
        retained = make_city_frame(["历史保留城市"], "2026-02-01")
        expanded = build_expanded(main, [retained])
        latest = expanded.groupby("城市")["日期"].max()
        self.assertEqual(latest["上海"], pd.Timestamp("2026-04-01"))
        self.assertEqual(
            latest["历史保留城市"], pd.Timestamp("2026-02-01")
        )

    def test_monitoring_rejects_incomplete_or_lagging_cross_section(self):
        cities = [
            city for tier_cities in MONITOR_CITIES.values()
            for city in tier_cities
        ]
        incomplete = make_city_frame(cities[:-1], include_tier=True)
        with self.assertRaisesRegex(ValueError, "城市覆盖不完整"):
            validate_monitoring_dataset(incomplete)

        lagging = make_city_frame(cities, include_tier=True)
        lagging.loc[lagging["城市"] == cities[-1], "日期"] = "2026-03-01"
        with self.assertRaisesRegex(ValueError, "最新观察期不一致"):
            generate_monitoring_report(lagging)

    def test_monitoring_rejects_empty_latest_key_and_wrong_tier(self):
        cities = [
            city for tier_cities in MONITOR_CITIES.values()
            for city in tier_cities
        ]
        frame = make_city_frame(cities, include_tier=True)
        frame.loc[frame["城市"] == "上海", PRICE_COLUMNS[0]] = None
        with self.assertRaisesRegex(ValueError, "最新期关键字段为空"):
            validate_monitoring_dataset(frame)

        frame = make_city_frame(cities, include_tier=True)
        frame.loc[frame["城市"] == "上海", "梯队"] = "T3"
        with self.assertRaisesRegex(ValueError, "梯队不一致"):
            validate_monitoring_dataset(frame)

    def test_monitoring_publish_failure_preserves_existing_file(self):
        cities = [
            city for tier_cities in MONITOR_CITIES.values()
            for city in tier_cities
        ]
        invalid = make_city_frame(cities[:-1], include_tier=True)
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "latest_data.csv"
            target.write_text("verified-old-data\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                publish_latest_data(invalid, target)
            self.assertEqual(
                target.read_text(encoding="utf-8"), "verified-old-data\n"
            )

    def test_atomic_csv_writes_use_unique_temporary_files(self):
        frame = make_city_frame(["上海"])
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "latest_data.csv"
            stale = Path(temp_dir) / "latest_data.csv.tmp"
            stale.write_text("another-writer", encoding="utf-8")
            atomic_write_csv(frame, target)
            published = pd.read_csv(target)
            self.assertEqual(published.iloc[0]["城市"], "上海")
            self.assertEqual(stale.read_text(encoding="utf-8"), "another-writer")

    def test_atomic_csv_concurrent_writers_never_publish_partial_data(self):
        frames = []
        for index in range(8):
            frame = make_city_frame(["上海"])
            frame["writer"] = index
            frames.append(frame)

        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "latest_data.csv"
            with ThreadPoolExecutor(max_workers=8) as executor:
                list(
                    executor.map(
                        lambda frame: atomic_write_csv(frame, target), frames
                    )
                )

            published = pd.read_csv(target)
            self.assertEqual(len(published), 1)
            self.assertEqual(published.iloc[0]["城市"], "上海")
            self.assertIn(int(published.iloc[0]["writer"]), range(8))
            self.assertEqual(list(Path(temp_dir).glob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
