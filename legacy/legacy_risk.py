#!/usr/bin/env python3
"""Archived city-risk score; execution and import are disabled."""

raise SystemExit(
    "DISABLED_LEGACY_RISK_SCORE: arbitrary weights and city indices cannot "
    "measure a specific property's investment risk"
)

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent


class RiskModel:
    """风险量化模型"""
    
    def __init__(self):
        self.weights = {
            'price_momentum': 0.25,  # 价格动量
            'volatility': 0.20,      # 波动率
            'drawdown': 0.20,        # 回撤幅度
            'recovery_speed': 0.15,  # 恢复速度
            'macro_risk': 0.20,      # 宏观风险
        }
    
    def calculate_risk_score(self, hp, city):
        """计算城市风险评分(0-100, 越高越危险)"""
        city_data = hp[hp['城市'] == city].sort_values('日期')
        if len(city_data) < 24:
            return None
        
        yoy = city_data['二手住宅价格指数-同比'].dropna()
        mom = city_data['二手住宅价格指数-环比'].dropna()
        
        if len(yoy) < 12 or len(mom) < 12:
            return None
        
        # 1. 价格动量(环比趋势)
        recent_mom = mom.tail(6).mean()
        momentum_score = max(0, min(100, (100 - recent_mom) * 50))
        
        # 2. 波动率
        vol = mom.tail(12).std()
        vol_score = min(100, vol * 100)
        
        # 3. 回撤幅度(从峰值到当前)
        peak = yoy.max()
        current = yoy.iloc[-1]
        drawdown = (peak - current) / peak * 100
        drawdown_score = min(100, drawdown * 2)
        
        # 4. 恢复速度(谷底到当前)
        trough = yoy.min()
        recovery = (current - trough) / (peak - trough) * 100 if peak > trough else 0
        recovery_score = max(0, 100 - recovery)
        
        # 5. 宏观风险(基于Regime)
        regime_score = 50  # 默认中等
        
        # 综合评分
        total = (
            momentum_score * self.weights['price_momentum'] +
            vol_score * self.weights['volatility'] +
            drawdown_score * self.weights['drawdown'] +
            recovery_score * self.weights['recovery_speed'] +
            regime_score * self.weights['macro_risk']
        )
        
        return {
            'city': city,
            'total_score': total,
            'momentum_score': momentum_score,
            'vol_score': vol_score,
            'drawdown_score': drawdown_score,
            'recovery_score': recovery_score,
            'regime_score': regime_score,
            'risk_level': self._risk_level(total),
        }
    
    def _risk_level(self, score):
        if score >= 70:
            return "🔴 高风险"
        elif score >= 50:
            return "🟠 中高风险"
        elif score >= 35:
            return "🟡 中等风险"
        elif score >= 20:
            return "🟢 低风险"
        else:
            return "🟢 极低风险"
    
    def calculate_all(self, hp, cities=None):
        """计算所有城市风险"""
        if cities is None:
            cities = hp['城市'].unique()
        
        results = []
        for city in cities:
            result = self.calculate_risk_score(hp, city)
            if result:
                results.append(result)
        
        return sorted(results, key=lambda x: x['total_score'], reverse=True)


def run_risk_analysis():
    """运行风险分析"""
    print("=" * 60)
    print("  退役原型 — 风险量化分析")
    print("=" * 60)
    
    hp = pd.read_csv(f"{OUTPUT}/70city_expanded.csv")
    hp['日期'] = pd.to_datetime(hp['日期'])
    hp = hp.drop_duplicates(subset=['城市', '日期'])
    
    model = RiskModel()
    results = model.calculate_all(hp)
    
    r = []
    r.append("# 退役原型风险量化报告\n")
    r.append(f"> {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    r.append("\n## 风险评分排名\n")
    r.append("| 排名 | 城市 | 总分 | 动量 | 波动 | 回撤 | 恢复 | 风险等级 |")
    r.append("|------|------|------|------|------|------|------|---------|")
    
    for i, res in enumerate(results[:30]):
        r.append(f"| {i+1} | {res['city']} | {res['total_score']:.0f} | {res['momentum_score']:.0f} | {res['vol_score']:.0f} | {res['drawdown_score']:.0f} | {res['recovery_score']:.0f} | {res['risk_level']} |")
    
    report = "\n".join(r)
    with open(f"{OUTPUT}/RISK_REPORT.md", "w") as f:
        f.write(report)
    print(f"报告已保存: {OUTPUT}/RISK_REPORT.md")
    print(f"大小: {len(report)}字符")


if __name__ == "__main__":
    run_risk_analysis()
