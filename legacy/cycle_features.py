#!/usr/bin/env python3
"""Archived heuristic cycle labels; execution and import are disabled."""

raise SystemExit(
    "DISABLED_LEGACY_CYCLE_FEATURES: arbitrary seasonal and volatility labels "
    "are not validated decision evidence"
)

import pandas as pd
import numpy as np
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent
hp = pd.read_csv(OUTPUT / "70city_expanded.csv")
hp['日期'] = pd.to_datetime(hp['日期'])
hp = hp.drop_duplicates(subset=['城市', '日期'])

def tier(city):
    if city in ['北京','上海','广州','深圳']: return 'T1'
    if city in ['天津','重庆','杭州','南京','武汉','成都','西安','长沙','郑州']: return 'T2'
    return 'T3'

hp['梯队'] = hp['城市'].apply(tier)
hp['month'] = hp['日期'].dt.month

r = []
r.append("# 📈 各城市周期特征分析\n")

# 季节性
r.append("## 季节性模式(2015-2025)\n")
mask = (hp['日期']<'2026-01') & (hp['日期']>='2015-01')
seasonal = hp[mask].groupby('month')['二手住宅价格指数-环比'].mean()
r.append("| 月份 | 二手环比均值 | 特征 |")
r.append("|------|-----------|------|")
for m, val in seasonal.items():
    feature = "🔥小阳春" if val>100.15 else "→平稳" if val>100 else "↓淡季"
    r.append(f"| {m}月 | {val:.2f} | {feature} |")

# 波动率
r.append("\n## 波动率排名\n")
r.append("| 城市 | 梯队 | 二手环比波动 | 活跃度 |")
r.append("|------|------|------------|--------|")

vol_data = []
for city in sorted(hp['城市'].unique()):
    cd = hp[hp['城市']==city].sort_values('日期').tail(12)
    if len(cd) < 6: continue
    uv = cd['二手住宅价格指数-环比'].std()
    vol_data.append({'city':city, 'tier':tier(city), 'uv':uv})

vol_df = pd.DataFrame(vol_data).sort_values('uv', ascending=False)
for _, row in vol_df.iterrows():
    active = "🔥高" if row['uv']>0.5 else "🟡中" if row['uv']>0.3 else "🟢低"
    r.append(f"| {row['city']} | {row['tier']} | {row['uv']:.2f} | {active} |")

report = "\n".join(r)
with open(OUTPUT / "CYCLE_FEATURES.md", "w", encoding="utf-8") as f:
    f.write(report)
print(f"报告: {len(report)}字符, {len(report.splitlines())}行")
