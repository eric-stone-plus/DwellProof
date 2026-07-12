#!/usr/bin/env python3
"""
房产卖/买决策评分器
基于 MAGI 三维度 + 领先指标体系
数据源: akshare (70城房价)
"""

import datetime
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

try:
    import akshare as ak
    import pandas as pd
except ImportError:
    print("需要安装依赖: pip install akshare pandas")
    sys.exit(1)


class Decision(Enum):
    SELL_NOW = "立即卖出"
    SELL_SOON = "近期卖出 (3个月内)"
    HOLD = "持有观望"
    BUY_NOW = "立即买入"
    BUY_WAIT = "等待时机"


@dataclass
class CityIndicators:
    """城市指标"""
    city: str
    month: str
    new_house_mom: float = 0    # 新房环比
    new_house_yoy: float = 0    # 新房同比
    second_house_mom: float = 0  # 二手房环比
    second_house_yoy: float = 0  # 二手房同比
    volume_index: float = 0     # 成交量指数


@dataclass
class DecisionScore:
    """决策评分"""
    city: str
    direction: str  # "sell" / "buy"
    total_score: float = 0      # -100 到 +100
    price_trend_score: float = 0  # 价格趋势
    volume_score: float = 0      # 成交量
    macro_score: float = 0       # 宏观环境
    season_score: float = 0      # 季节因子
    recommendation: Decision = Decision.HOLD
    reasoning: list = None

    def __post_init__(self):
        if self.reasoning is None:
            self.reasoning = []


def fetch_city_price(city: str) -> CityIndicators:
    """获取城市房价数据"""
    try:
        df = ak.house_price_city(city=city)
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            return CityIndicators(
                city=city,
                month=str(latest.get("月份", "")),
                new_house_mom=float(latest.get("新房环比", 0) or 0),
                new_house_yoy=float(latest.get("新房同比", 0) or 0),
                second_house_mom=float(latest.get("二手房环比", 0) or 0),
                second_house_yoy=float(latest.get("二手房同比", 0) or 0),
            )
    except Exception as e:
        print(f"[WARN] {city} 数据获取失败: {e}")
    return CityIndicators(city=city, month="N/A")


def fetch_70city_index():
    """获取70城房价指数"""
    try:
        df = ak.house_price_city()
        return df
    except Exception as e:
        print(f"[WARN] 70城数据获取失败: {e}")
        return None


def get_season_factor(month: int) -> float:
    """
    季节因子: 最佳卖房月份
    3月 > 4月 > 5月 > 9月 > 10月 > 其他
    上海二手环比是全国领先指标 (2-5月)
    """
    factors = {
        1: -15,   # 春节淡季
        2: -10,   # 春节淡季
        3: 25,    # 最佳卖房月
        4: 20,    # 次优
        5: 15,    # 次优
        6: 5,
        7: -5,
        8: -5,
        9: 10,    # 金九
        10: 10,   # 银十
        11: 0,
        12: -5,
    }
    return factors.get(month, 0)


def score_sell_decision(indicators: CityIndicators) -> DecisionScore:
    """卖房决策评分"""
    score = DecisionScore(city=indicators.city, direction="sell")
    total = 0

    # 1. 价格趋势 (40%)
    # 环比转正→不适合卖(还会涨); 环比持续下跌→赶紧卖
    mom = indicators.second_house_mom
    if mom > 0:
        price_score = -20  # 还在涨, 不急卖
        score.reasoning.append(f"二手房环比 +{mom}% → 价格上行, 不急卖")
    elif mom > -0.5:
        price_score = 0
        score.reasoning.append(f"二手房环比 {mom}% → 基本持平")
    elif mom > -1:
        price_score = 15
        score.reasoning.append(f"二手房环比 {mom}% → 温和下跌, 可考虑卖")
    else:
        price_score = 30
        score.reasoning.append(f"二手房环比 {mom}% → 明显下跌, 建议尽快卖")
    total += price_score

    # 2. 同比趋势 (20%)
    yoy = indicators.second_house_yoy
    if yoy < -5:
        yoy_score = 15
        score.reasoning.append(f"二手房同比 {yoy}% → 年度跌幅大, 价格压力大")
    elif yoy < 0:
        yoy_score = 5
    elif yoy < 5:
        yoy_score = -5
    else:
        yoy_score = -10
        score.reasoning.append(f"二手房同比 +{yoy}% → 年度涨幅可观, 可持有")
    total += yoy_score

    # 3. 季节因子 (15%)
    now = datetime.datetime.now()
    season = get_season_factor(now.month)
    total += season
    if abs(season) > 10:
        month_name = f"{now.month}月"
        score.reasoning.append(f"季节因子: {month_name} = {season:+d}分")

    # 4. 新房vs二手房分化 (15%)
    new_mom = indicators.new_house_mom
    if new_mom > mom + 0.5:
        spread_score = 5  # 新房比二手涨得快→二手压力
        score.reasoning.append("新房涨幅>二手 → 二手竞争压力")
    elif mom > new_mom + 0.5:
        spread_score = -5  # 二手比新房涨得快→二手还有空间
    else:
        spread_score = 0
    total += spread_score

    # 5. 城市特殊因子 (10%)
    if indicators.city == "上海":
        # 上海二手环比是全国领先指标 (2-5月)
        if now.month in [2, 3, 4, 5]:
            total += 10
            score.reasoning.append("上海2-5月: 全国领先指标窗口期")
    elif indicators.city in ["广州", "深圳"]:
        total += 5
        score.reasoning.append(f"{indicators.city}: 一线城市流动性好")

    score.total_score = total
    score.price_trend_score = price_score
    score.season_score = season

    # 决策
    if total >= 40:
        score.recommendation = Decision.SELL_NOW
    elif total >= 20:
        score.recommendation = Decision.SELL_SOON
    elif total >= -20:
        score.recommendation = Decision.HOLD
    else:
        score.recommendation = Decision.HOLD

    return score


def format_decision(score: DecisionScore) -> str:
    """格式化决策报告"""
    lines = [
        f"=== {score.city} 房产决策评分 ===",
        f"总分: {score.total_score:+.0f} / 100",
        f"建议: {score.recommendation.value}",
        "",
        "分析依据:",
    ]
    for r in score.reasoning:
        lines.append(f"  • {r}")
    lines.append("")
    lines.append(f"价格趋势分: {score.price_trend_score:+.0f}")
    lines.append(f"季节因子分: {score.season_score:+.0f}")
    return "\n".join(lines)


def batch_score(cities: list, direction: str = "sell"):
    """批量评分"""
    results = []
    for city in cities:
        indicators = fetch_city_price(city)
        if direction == "sell":
            score = score_sell_decision(indicators)
        else:
            score = score_sell_decision(indicators)  # 买方逻辑简化
        results.append(score)
        print(format_decision(score))
        print()
    return results


if __name__ == "__main__":
    cities = ["广州", "长春", "上海", "北京", "深圳"]
    print("=== 房产卖方决策批量评分 ===\n")
    batch_score(cities, "sell")
