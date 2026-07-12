#!/usr/bin/env python3
"""Legacy MCP compatibility layer exposing city-index market context only."""

import json
from pathlib import Path
from typing import Any, Dict, List


OUTPUT = Path(__file__).resolve().parent
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
MARKET_CONTEXT_ONLY = "MARKET_CONTEXT_ONLY"
MARKET_CONTEXT_CAUTION = (
    "城市价格指数仅为描述性市场背景，不能替代标的成交案例、产权核验、"
    "税费、融资报价或全成本现金流。"
)


class LegacyMarketContextMCP:
    """Expose non-actionable observations while preserving legacy aliases."""

    def __init__(self):
        self.tools = self.register_tools()

    def register_tools(self) -> Dict[str, Dict]:
        """Register safe context tools and explicit deprecated aliases."""
        city_schema = {
            "city": {"type": "string", "description": "城市名称"},
        }
        return {
            "housing_get_city_data": {
                "description": "获取配置城市的价格指数背景；输出不可操作",
                "input_schema": city_schema,
                "execute": self.get_city_data,
                "deprecated": False,
            },
            "housing_get_market_snapshot": {
                "description": "获取旧数据集中配置城市的同期指数截面；非全国结论",
                "input_schema": {},
                "execute": self.get_market_snapshot,
                "deprecated": False,
            },
            "housing_compare_cities": {
                "description": "并列展示多个城市的价格指数背景；不生成排序或动作",
                "input_schema": {
                    "cities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "城市列表",
                    },
                },
                "execute": self.compare_cities,
                "deprecated": False,
            },
            "housing_get_shanghai_observation": {
                "description": "获取上海价格指数观察值；不外推其他城市",
                "input_schema": {},
                "execute": self.get_shanghai_observation,
                "deprecated": False,
            },
            "housing_get_seasonality_context": {
                "description": "获取历史月度指数均值；不解释为交易月份",
                "input_schema": city_schema,
                "execute": self.get_seasonality_context,
                "deprecated": False,
            },
            "housing_get_national_summary": {
                "description": "已弃用兼容别名；返回配置城市指数截面而非全国结论",
                "input_schema": {},
                "execute": self.get_national_summary,
                "deprecated": True,
            },
            "housing_get_buy_signal": {
                "description": "已弃用兼容别名；仅返回证据不足，不生成方向性动作",
                "input_schema": city_schema,
                "execute": self.get_buy_signal,
                "deprecated": True,
            },
            "housing_get_sell_signal": {
                "description": "已弃用兼容别名；仅返回证据不足，不生成方向性动作",
                "input_schema": city_schema,
                "execute": self.get_sell_signal,
                "deprecated": True,
            },
            "housing_get_leading_indicator": {
                "description": "已弃用兼容别名；仅返回证据不足，不生成跨城市推断",
                "input_schema": {},
                "execute": self.get_leading_indicator,
                "deprecated": True,
            },
            "housing_get_seasonal_pattern": {
                "description": "已弃用兼容别名；仅返回证据不足，不生成交易窗口",
                "input_schema": city_schema,
                "execute": self.get_seasonal_pattern,
                "deprecated": True,
            },
            "housing_get_investment_ranking": {
                "description": "已弃用兼容别名；仅返回证据不足，不生成城市排序",
                "input_schema": {},
                "execute": self.get_investment_ranking,
                "deprecated": True,
            },
        }

    @staticmethod
    def _load_city_indices():
        import pandas as pd

        frame = pd.read_csv(OUTPUT / "70city_expanded.csv")
        frame["日期"] = pd.to_datetime(frame["日期"])
        return frame.drop_duplicates(["城市", "日期"])

    @staticmethod
    def _error(message: str) -> Dict:
        return {
            "error": message,
            "status": INSUFFICIENT_EVIDENCE,
            "actionable": False,
        }

    @staticmethod
    def _deprecated_refusal(
        alias: str,
        replacement: str,
        *,
        market_context: Dict | None = None,
        error: str | None = None,
        extra: Dict | None = None,
    ) -> Dict:
        result = {
            "status": INSUFFICIENT_EVIDENCE,
            "actionable": False,
            "deprecated": True,
            "alias": alias,
            "replacement": replacement,
            "reason": (
                "旧接口已停用；现有城市指数不足以形成标的级方向判断，"
                "请补充可比成交、产权、税费、融资和全成本证据。"
            ),
        }
        if market_context is not None:
            result["market_context"] = market_context
        if error is not None:
            result["error"] = error
        if extra:
            result.update(extra)
        return result

    def get_city_data(self, city: str) -> Dict:
        """Return one configured city's descriptive index observations."""
        hp = self._load_city_indices()
        city_data = hp[hp["城市"] == city].sort_values("日期")
        if city_data.empty:
            return self._error(f"城市 {city} 不存在")

        latest = city_data.iloc[-1]
        recent6 = city_data.tail(6)
        return {
            "city": city,
            "date": latest["日期"].strftime("%Y-%m"),
            "new_house": {
                "yoy": float(latest["新建商品住宅价格指数-同比"]),
                "mom": float(latest["新建商品住宅价格指数-环比"]),
            },
            "used_house": {
                "yoy": float(latest["二手住宅价格指数-同比"]),
                "mom": float(latest["二手住宅价格指数-环比"]),
            },
            "recent_6m_index_average": {
                "new_mom": float(
                    recent6["新建商品住宅价格指数-环比"].mean()
                ),
                "used_mom": float(
                    recent6["二手住宅价格指数-环比"].mean()
                ),
            },
            "status": MARKET_CONTEXT_ONLY,
            "actionable": False,
            "role": "city_index_market_context",
            "source_state": "legacy_local_dataset_not_fully_verified",
            "caution": MARKET_CONTEXT_CAUTION,
        }

    def get_market_snapshot(self) -> Dict:
        """Summarize the configured legacy-city set without national claims."""
        hp = self._load_city_indices()
        latest_date = hp["日期"].max()
        latest = hp[hp["日期"] == latest_date].copy()
        if latest.empty:
            return self._error("配置城市指数截面为空")

        def tier(city):
            if city in ["北京", "上海", "广州", "深圳"]:
                return "T1"
            if city in [
                "天津", "重庆", "杭州", "南京", "武汉", "成都", "西安",
                "长沙", "郑州",
            ]:
                return "T2"
            return "T3"

        latest["梯队"] = latest["城市"].apply(tier)
        summary = {}
        for tier_name in ["T1", "T2", "T3"]:
            tier_data = latest[latest["梯队"] == tier_name]
            summary[tier_name] = {
                "city_count": len(tier_data),
                "new_mom_avg": float(
                    tier_data["新建商品住宅价格指数-环比"].mean()
                ),
                "used_mom_avg": float(
                    tier_data["二手住宅价格指数-环比"].mean()
                ),
                "new_yoy_avg": float(
                    tier_data["新建商品住宅价格指数-同比"].mean()
                ),
                "used_yoy_avg": float(
                    tier_data["二手住宅价格指数-同比"].mean()
                ),
            }
        return {
            "date": latest_date.strftime("%Y-%m"),
            "coverage": "legacy_configured_city_set",
            "city_count_at_latest_period": len(latest),
            "tiers": summary,
            "status": MARKET_CONTEXT_ONLY,
            "actionable": False,
            "source_state": "legacy_local_dataset_not_fully_verified",
            "caution": MARKET_CONTEXT_CAUTION,
        }

    def get_national_summary(self) -> Dict:
        """Compatibility alias; the underlying data is not a national summary."""
        result = self.get_market_snapshot()
        result.update(
            {
                "deprecated": True,
                "alias": "housing_get_national_summary",
                "replacement": "housing_get_market_snapshot",
            }
        )
        return result

    def compare_cities(self, cities: List[str]) -> Dict:
        """Return parallel city contexts without ranking them."""
        results = {}
        for city in cities:
            data = self.get_city_data(city)
            if "error" not in data:
                results[city] = data
        return results

    def get_shanghai_observation(self) -> Dict:
        """Return Shanghai's latest value without a cross-city inference."""
        data = self.get_city_data("上海")
        if "error" in data:
            return data
        return {
            "observation": "上海二手住宅价格指数环比",
            "date": data["date"],
            "value": data["used_house"]["mom"],
            "status": MARKET_CONTEXT_ONLY,
            "actionable": False,
            "note": "探索性城市观察；未完成样本外验证，不得外推其他城市。",
            "market_context": data,
        }

    def get_seasonality_context(self, city: str) -> Dict:
        """Return historical monthly averages without selecting a trade month."""
        hp = self._load_city_indices()
        city_data = hp[(hp["城市"] == city) & (hp["日期"] >= "2015-01-01")].copy()
        if city_data.empty:
            return self._error(f"城市 {city} 的历史月度数据不足")
        city_data["month"] = city_data["日期"].dt.month
        monthly = city_data.groupby("month")["二手住宅价格指数-环比"].mean()
        return {
            "city": city,
            "observation_start": city_data["日期"].min().strftime("%Y-%m"),
            "observation_end": city_data["日期"].max().strftime("%Y-%m"),
            "monthly_index_averages": {
                int(month): float(value) for month, value in monthly.items()
            },
            "status": MARKET_CONTEXT_ONLY,
            "actionable": False,
            "note": "历史月度均值仅描述样本，不代表未来走势或交易月份。",
        }

    def get_buy_signal(self, city: str) -> Dict:
        data = self.get_city_data(city)
        return self._deprecated_refusal(
            "housing_get_buy_signal",
            "housing_get_city_data",
            market_context=None if "error" in data else data,
            error=data.get("error"),
        )

    def get_sell_signal(self, city: str) -> Dict:
        data = self.get_city_data(city)
        return self._deprecated_refusal(
            "housing_get_sell_signal",
            "housing_get_city_data",
            market_context=None if "error" in data else data,
            error=data.get("error"),
        )

    def get_leading_indicator(self) -> Dict:
        data = self.get_shanghai_observation()
        return self._deprecated_refusal(
            "housing_get_leading_indicator",
            "housing_get_shanghai_observation",
            market_context=None if "error" in data else data,
            error=data.get("error"),
        )

    def get_seasonal_pattern(self, city: str) -> Dict:
        data = self.get_seasonality_context(city)
        return self._deprecated_refusal(
            "housing_get_seasonal_pattern",
            "housing_get_seasonality_context",
            market_context=None if "error" in data else data,
            error=data.get("error"),
        )

    def get_investment_ranking(self) -> Dict:
        return self._deprecated_refusal(
            "housing_get_investment_ranking",
            "DwellProof property-level evidence workbench",
            extra={"ranking": []},
        )

    def list_tools(self) -> List[Dict]:
        """List tools with deprecation state visible to callers."""
        return [
            {
                "name": name,
                "description": tool["description"],
                "input_schema": tool["input_schema"],
                "deprecated": tool.get("deprecated", False),
            }
            for name, tool in self.tools.items()
        ]

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        if tool_name not in self.tools:
            return self._error(f"工具 {tool_name} 不存在")
        return self.tools[tool_name]["execute"](**kwargs)


def demo():
    """Print only the safe market-context tools."""
    mcp = LegacyMarketContextMCP()
    print("Retired prototype market-context MCP demo")
    for tool in mcp.list_tools():
        if not tool["deprecated"]:
            print(f"  {tool['name']}: {tool['description']}")
    print(json.dumps(mcp.get_city_data("广州"), indent=2, ensure_ascii=False))
    print(json.dumps(mcp.get_shanghai_observation(), indent=2, ensure_ascii=False))
    print(json.dumps(mcp.get_seasonality_context("广州"), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    demo()
