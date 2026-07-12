from __future__ import annotations

import csv
import json
import unittest
from decimal import Decimal
from pathlib import Path

from core.tax import (
    NATIONAL_DEED_TAX_EFFECTIVE_FROM,
    NATIONAL_DEED_TAX_RULE_ID,
    NATIONAL_DEED_TAX_SOURCE_URL,
)


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOTS = ROOT / "docs" / "research" / "snapshots"


class OfficialSnapshotTests(unittest.TestCase):
    def test_tax_snapshot_matches_implemented_rule(self) -> None:
        snapshot = json.loads((SNAPSHOTS / "tax-cn-2024-12-01.json").read_text())
        self.assertEqual("2024-12-01", NATIONAL_DEED_TAX_EFFECTIVE_FROM.isoformat())
        self.assertEqual(NATIONAL_DEED_TAX_SOURCE_URL, snapshot["source_url"])
        self.assertEqual("2024-12-01", snapshot["effective_from"])
        self.assertEqual(
            Decimal("0.01"),
            Decimal(str(snapshot["deed_tax"]["family_only_home"]["area_lte_140_rate"])),
        )
        self.assertEqual(
            Decimal("0.015"),
            Decimal(str(snapshot["deed_tax"]["family_only_home"]["area_gt_140_rate"])),
        )
        self.assertEqual(
            Decimal("0.01"),
            Decimal(str(snapshot["deed_tax"]["family_second_home"]["area_lte_140_rate"])),
        )
        self.assertEqual(
            Decimal("0.02"),
            Decimal(str(snapshot["deed_tax"]["family_second_home"]["area_gt_140_rate"])),
        )
        self.assertEqual("CN-DEED-TAX-2024-12-01-v1", NATIONAL_DEED_TAX_RULE_ID)

    def test_selected_nbs_snapshot_still_matches_local_csv(self) -> None:
        snapshot = json.loads(
            (SNAPSHOTS / "nbs-70city-2026-04-selected.json").read_text()
        )
        self.assertTrue(snapshot["all_match"])
        self.assertEqual("previous_month=100", snapshot["comparison_bases"]["mom_index"])
        self.assertEqual(
            "previous_year_month=100", snapshot["comparison_bases"]["yoy_index"]
        )

        local: dict[str, dict[str, float]] = {}
        with (ROOT / "legacy" / "70city_expanded.csv").open(
            encoding="utf-8-sig", newline=""
        ) as handle:
            for row in csv.DictReader(handle):
                if row["日期"] != snapshot["observation_date"]:
                    continue
                local[row["城市"]] = {
                    "mom_index": float(row["二手住宅价格指数-环比"]),
                    "yoy_index": float(row["二手住宅价格指数-同比"]),
                }

        self.assertEqual(5, len(snapshot["checks"]))
        for check in snapshot["checks"]:
            with self.subTest(city=check["city"]):
                self.assertTrue(check["matches"])
                self.assertEqual(check["official"], check["local"])
                self.assertEqual(check["local"], local[check["city"]])

    def test_lpr_snapshot_is_explicitly_benchmark_only(self) -> None:
        snapshot = json.loads((SNAPSHOTS / "pbc-lpr-2026-06-22.json").read_text())
        self.assertEqual(3.0, snapshot["values"]["lpr_1y_percent"])
        self.assertEqual(3.5, snapshot["values"]["lpr_5y_plus_percent"])
        self.assertEqual(
            "benchmark_only_not_the_user_mortgage_execution_rate",
            snapshot["product_constraint"],
        )


if __name__ == "__main__":
    unittest.main()
