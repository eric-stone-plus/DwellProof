#!/usr/bin/env python3
"""Cross-check selected local rows against an official NBS HTML table.

This script intentionally uses only the Python standard library. It fails closed
if the official table shape, comparison bases, selected cities, or local values
do not match the expected contract.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen


DEFAULT_URL = "https://www.stats.gov.cn/sj/zxfb/202605/t20260518_1963715.html"
DEFAULT_CSV = Path(__file__).resolve().parents[1] / "legacy" / "70city_expanded.csv"
DEFAULT_CITIES = ("北京", "上海", "广州", "深圳", "武汉")


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tables: list[list[list[str]]] = []
        self._table: list[list[str]] | None = None
        self._row: list[str] | None = None
        self._cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"td", "th"} and self._row is not None:
            self._cell = []

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if text and self._cell is not None:
            self._cell.append(text)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._cell is not None:
            assert self._row is not None
            self._row.append("".join(self._cell))
            self._cell = None
        elif tag == "tr" and self._row is not None:
            assert self._table is not None
            if self._row:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None


def fetch(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": "DwellProof source verifier/0.1"})
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"official page returned HTTP {response.status}")
        return response.read()


def find_used_home_table(html: str) -> list[list[str]]:
    parser = TableParser()
    parser.feed(html)
    expected_header = ["城市", "环比", "同比", "1-4月平均", "城市", "环比", "同比", "1-4月平均"]
    expected_bases = ["上月=100", "上年同月=100", "上年同期=100"] * 2
    candidates = [
        table
        for table in parser.tables
        if len(table) >= 37 and table[0] == expected_header and table[1] == expected_bases
    ]
    if len(candidates) < 2:
        raise RuntimeError("official page no longer has the expected new/used-home table pair")
    return candidates[1]


def official_rows(table: list[list[str]]) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    for row in table[2:]:
        for offset in (0, 4):
            if len(row) < offset + 4:
                continue
            city = row[offset].replace(" ", "")
            result[city] = {
                "mom_index": float(row[offset + 1]),
                "yoy_index": float(row[offset + 2]),
                "year_to_date_index": float(row[offset + 3]),
            }
    return result


def local_rows(path: Path, observation_date: str) -> dict[str, dict[str, float]]:
    result: dict[str, dict[str, float]] = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row["日期"] != observation_date:
                continue
            result[row["城市"]] = {
                "mom_index": float(row["二手住宅价格指数-环比"]),
                "yoy_index": float(row["二手住宅价格指数-同比"]),
            }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--observation-date", default="2026-04-01")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    raw = fetch(args.url)
    official = official_rows(find_used_home_table(raw.decode("utf-8", "replace")))
    local = local_rows(args.csv, args.observation_date)
    checks = []
    for city in DEFAULT_CITIES:
        if city not in official or city not in local:
            raise RuntimeError(f"missing selected city: {city}")
        matches = (
            official[city]["mom_index"] == local[city]["mom_index"]
            and official[city]["yoy_index"] == local[city]["yoy_index"]
        )
        checks.append({"city": city, "official": official[city], "local": local[city], "matches": matches})

    result = {
        "schema_version": "official-source-check.v1",
        "source_url": args.url,
        "source_authority": "National Bureau of Statistics of China",
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "observation_date": args.observation_date,
        "comparison_bases": {"mom_index": "previous_month=100", "yoy_index": "previous_year_month=100"},
        "local_file": str(args.csv),
        "checks": checks,
        "all_match": all(check["matches"] for check in checks),
    }
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
