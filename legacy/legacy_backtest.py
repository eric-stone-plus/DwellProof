#!/usr/bin/env python3
"""
退役原型 — 历史回测框架
验证预测模型的准确性
"""

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self):
        self.results = []
    
    def backtest_leading_indicator(self, hp, lead_city='上海', test_cities=None):
        """Refuse the legacy same-sample lead rule as a validated backtest."""
        return {
            'status': 'disabled',
            'actionable': False,
            'results': {},
            'reason': '缺少朴素基线、预注册规则和样本外验证，不能报告准确率',
        }
    
    def backtest_buy_signal(self, hp, city, start_date='2020-01-01'):
        """
        旧买入回测已停用。

        原实现把六个月后同比跌幅收窄当作投资成功，未计算成交价、
        租金、税费、融资成本或退出价格，不能称为投资收益回测。
        """
        return {
            'city': city,
            'status': 'disabled',
            'actionable': False,
            'reason': '缺少标的级现金流和全成本数据，不能计算投资收益',
        }
    
    def backtest_sell_signal(self, hp, city, start_date='2020-01-01'):
        """
        旧卖出回测已停用。

        原实现的触发条件与生产卖房规则方向相反，也未使用实际卖出价
        和持有成本，不能用于证明卖出建议准确。
        """
        return {
            'city': city,
            'status': 'disabled',
            'actionable': False,
            'reason': '生产规则已停用，且缺少实际卖出净收益数据',
        }


def run_backtest():
    """运行回测"""
    print("=" * 60)
    print("  退役原型 — 历史回测")
    print("=" * 60)
    
    hp = pd.read_csv(OUTPUT / "70city_expanded.csv")
    hp['日期'] = pd.to_datetime(hp['日期'])
    hp = hp.drop_duplicates(subset=['城市', '日期'])
    
    engine = BacktestEngine()
    r = [
        "> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | "
        "`actionable: false`  ",
        "> 本文件来自已退役的原 HouseAlice 原型，不属于 DwellProof。内容未经标的、产权、"
        "税费、贷款及成交证据核验，不得用于买卖、估值、预测、排名或风险判断。"
        "DwellProof 入口：`../web/`。\n",
    ]
    r.append("# 退役原型历史回测报告\n")
    r.append(f"> {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # 1. 领先指标回测
    r.append("\n## 一、上海领先指标回测\n")
    lead_results = engine.backtest_leading_indicator(hp)
    r.append(f"**已停用：{lead_results['reason']}。**")
    
    # 2. 买房信号回测
    r.append("\n## 二、买房信号回测\n")
    r.append("**已停用：旧指标未计算标的成交价、租金、税费、融资和退出成本，不能报告投资准确率。**")
    
    # 3. 卖房信号回测
    r.append("\n## 三、卖房信号回测\n")
    r.append("**已停用：旧回测阈值与生产规则相反，且没有实际卖出净收益数据。**")
    
    # 4. 结论
    r.append("\n## 四、结论\n")
    r.append("- 上海领先关系仅是探索性同向分类统计，未设置朴素基线和样本外验证，不能视为已验证")
    r.append("- 买入和卖出准确率均停用，待接入标的级全成本现金流后重建")
    r.append("- 回测结果仅供参考，不代表未来表现")
    
    report = "\n".join(r)
    with open(OUTPUT / "BACKTEST_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"报告已保存: {OUTPUT / 'BACKTEST_REPORT.md'}")
    print(f"大小: {len(report)}字符")


if __name__ == "__main__":
    run_backtest()
