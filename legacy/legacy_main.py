#!/usr/bin/env python3
"""Legacy compatibility report limited to descriptive market context."""

from datetime import datetime
from pathlib import Path


OUTPUT = Path(__file__).resolve().parent

from legacy_alert import AlertEngine
from legacy_decision import DecisionEngine
from legacy_mcp import LegacyMarketContextMCP
from legacy_uha import UnifiedHousingAccount


class LegacyMarketContext:
    """Legacy shell that never emits a directional transaction conclusion."""

    def __init__(self, name: str = "Retired housing prototype"):
        self.name = name
        self.uha = UnifiedHousingAccount.load()
        self.alert = AlertEngine()
        self.decision = DecisionEngine()
        self.mcp = LegacyMarketContextMCP()
        self.created_at = datetime.now().isoformat()

    def dashboard(self) -> str:
        """Generate a compatibility report with fail-closed semantics."""
        r = [
            "> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | "
            "`actionable: false`  ",
            "> 本文件来自已退役的原 HouseAlice 原型，不属于 DwellProof。内容未经标的、产权、"
            "税费、贷款及成交证据核验，不得用于买卖、估值、预测、排名或风险判断。"
            "DwellProof 入口：`../web/`.\n",
            f"# {self.name} - legacy market context\n",
            f"> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "> `INSUFFICIENT_EVIDENCE` | `actionable: false`",
            (
                "> This report displays legacy city-index observations only. "
                "Use the new `web/` workbench for property-level evidence; city "
                "indices do not support a buy, sell, hold, timing, or ranking action."
            ),
        ]

        shanghai = self.mcp.call_tool("housing_get_shanghai_observation")
        r.extend(
            [
                "\n## Shanghai index observation\n",
                f"- Period: {shanghai.get('date', 'unavailable')}",
                f"- Used-home MoM index: {shanghai.get('value', 'unavailable')}",
                f"- State: `{shanghai.get('status', 'INSUFFICIENT_EVIDENCE')}`",
                f"- Boundary: {shanghai.get('note', 'No cross-city inference')}",
            ]
        )

        snapshot = self.mcp.call_tool("housing_get_market_snapshot")
        r.extend(
            [
                "\n## Configured-city index snapshot\n",
                (
                    f"> Period: {snapshot.get('date', 'unavailable')} | "
                    f"Coverage: {snapshot.get('coverage', 'unavailable')} | "
                    f"Rows at period: {snapshot.get('city_count_at_latest_period', 0)}"
                ),
                "| Group | City rows | New MoM | Used MoM | New YoY | Used YoY |",
                "|---|---:|---:|---:|---:|---:|",
            ]
        )
        for tier, data in snapshot.get("tiers", {}).items():
            r.append(
                f"| {tier} | {data['city_count']} | {data['new_mom_avg']:.2f} | "
                f"{data['used_mom_avg']:.2f} | {data['new_yoy_avg']:.1f} | "
                f"{data['used_yoy_avg']:.1f} |"
            )
        r.append(f"\n- Caution: {snapshot.get('caution', 'Evidence unavailable')}")

        seasonal = self.mcp.call_tool(
            "housing_get_seasonality_context", city="广州"
        )
        r.extend(
            [
                "\n## Guangzhou historical monthly index context\n",
                (
                    f"> Sample: {seasonal.get('observation_start', 'unavailable')} "
                    f"to {seasonal.get('observation_end', 'unavailable')}"
                ),
                "| Month | Mean used-home MoM index |",
                "|---:|---:|",
            ]
        )
        for month, value in seasonal.get("monthly_index_averages", {}).items():
            r.append(f"| {month} | {value:.2f} |")
        r.append(f"\n- Boundary: {seasonal.get('note', 'No timing inference')}")

        r.extend(["\n## Local portfolio evidence state\n"])
        if self.uha.properties:
            r.append("- Status: PERSONAL_STATE_UNVERIFIED")
            r.append(
                "- Legacy local records are quarantined because their identity, "
                "source, and authenticity were never verified."
            )
            r.append("- Property count, costs, values, rent, and returns are not shown.")
        else:
            r.append("- No local property record")

        if self.uha.watchlist:
            r.extend(
                [
                    "\n## Watchlist state\n",
                    "- PERSONAL_STATE_UNVERIFIED; legacy notes are not displayed.",
                ]
            )

        return "\n".join(r)

    def full_report(self) -> str:
        """Append a parallel city-index table without ranking the cities."""
        r = [self.dashboard(), "\n\n---\n", "## Parallel city-index context\n"]
        comparison = self.mcp.call_tool(
            "housing_compare_cities", cities=["上海", "北京", "广州", "深圳"]
        )
        r.extend(
            [
                "| City | Period | New YoY | New MoM | Used YoY | Used MoM |",
                "|---|---|---:|---:|---:|---:|",
            ]
        )
        for city, data in comparison.items():
            r.append(
                f"| {city} | {data['date']} | {data['new_house']['yoy']:.1f} | "
                f"{data['new_house']['mom']:.1f} | {data['used_house']['yoy']:.1f} | "
                f"{data['used_house']['mom']:.1f} |"
            )
        r.append("\nNo row is a recommendation, forecast, or property valuation.")
        return "\n".join(r)

    def save_report(self):
        report = self.full_report()
        path = OUTPUT / "LEGACY_MARKET_CONTEXT.md"
        path.write_text(report, encoding="utf-8")
        print(f"Legacy market-context report saved: {path}")
        return path


def main():
    print("Retired prototype market-context compatibility report")
    archive = LegacyMarketContext()
    print(archive.dashboard())
    path = archive.save_report()
    print(f"\nReport: {path}")


if __name__ == "__main__":
    main()
