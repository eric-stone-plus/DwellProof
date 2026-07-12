#!/usr/bin/env python3
"""Archived city ranking; execution and import are disabled."""

raise SystemExit(
    "DISABLED_LEGACY_CITY_RANKING: city-index ordering is not a property "
    "investment or risk ranking"
)

import pandas as pd
import numpy as np
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent
df = pd.read_csv(f"{OUTPUT}/70city_expanded.csv")
df['日期'] = pd.to_datetime(df['日期'])

# 去重
df = df.drop_duplicates(subset=['城市', '日期'])

# 梯队
def tier(city):
    if city in ['北京','上海','广州','深圳']: return 'T1'
    if city in ['天津','重庆','杭州','南京','武汉','成都','西安','长沙','郑州']: return 'T2'
    return 'T3'

df['梯队'] = df['城市'].apply(tier)

latest = df[df['日期'] == df['日期'].max()]

r = []
r.append("# 📊 63城全量排名 + 详细周期分析\n")
r.append(f"> MAGI v1.0 | {df['城市'].nunique()}城 × {len(df)}条")

# === 1. 全量排名 ===
r.append("\n## 一、63城二手房环比排名\n")
r.append("| 排名 | 城市 | 梯队 | 环比 | 同比 | 市场背景 |")
r.append("|------|------|------|------|------|------|")

ranked = latest.sort_values('二手住宅价格指数-环比', ascending=False)
for i, (_, row) in enumerate(ranked.iterrows(), 1):
    mom = row['二手住宅价格指数-环比']
    yoy = row['二手住宅价格指数-同比']
    if mom >= 100.0: sig = "环比不低于100"
    elif mom >= 99.5: sig = "接近持平"
    else: sig = "环比低于99.5"
    r.append(f"| {i} | {row['城市']} | {row['梯队']} | {mom:.1f} | {yoy:.1f} | {sig} |")

# === 2. 同比排名 ===
r.append("\n## 二、63城二手房同比排名\n")
r.append("| 排名 | 城市 | 梯队 | 同比 | 环比 | 跌幅 |")
r.append("|------|------|------|------|------|------|")

ranked_yoy = latest.sort_values('二手住宅价格指数-同比', ascending=True)
for i, (_, row) in enumerate(ranked_yoy.iterrows(), 1):
    yoy = row['二手住宅价格指数-同比']
    mom = row['二手住宅价格指数-环比']
    decline = 100 - yoy
    r.append(f"| {i} | {row['城市']} | {row['梯队']} | {yoy:.1f} | {mom:.1f} | {decline:.1f}% |")

# === 3. 各城市谷底分析 ===
r.append("\n## 三、各城市谷底分析\n")
r.append("| 城市 | 梯队 | 谷底月 | 谷底值 | 当前值 | 回升幅度 | 距峰值 |")
r.append("|------|------|--------|--------|--------|---------|--------|")

for city in sorted(latest['城市'].unique()):
    cd = df[df['城市']==city].sort_values('日期')
    if len(cd) < 24: continue
    
    yoy_series = cd['二手住宅价格指数-同比'].dropna()
    if len(yoy_series) < 12: continue
    
    trough_val = yoy_series.min()
    trough_date = cd.loc[yoy_series.idxmin(), '日期'].strftime('%Y-%m')
    current_val = yoy_series.iloc[-1]
    peak_val = yoy_series.max()
    recovery = current_val - trough_val
    from_peak = peak_val - current_val
    
    r.append(f"| {city} | {tier(city)} | {trough_date} | {trough_val:.1f} | {current_val:.1f} | +{recovery:.1f} | -{from_peak:.1f} |")

# === 4. 环比趋势分析 ===
r.append("\n## 四、近6月环比趋势\n")
r.append("| 城市 | 1月 | 2月 | 3月 | 4月 | 趋势 |")
r.append("|------|-----|-----|-----|-----|------|")

for city in ['上海','北京','广州','深圳','杭州','成都','武汉','南京','天津','重庆','西安','郑州','长沙','长春']:
    cd = df[df['城市']==city].sort_values('日期').tail(6)
    if len(cd) < 6: continue
    vals = cd['二手住宅价格指数-环比'].values
    trend = "↑↑" if vals[-1] > vals[-3] and vals[-1] > 100 else "↑" if vals[-1] > vals[-3] else "↓" if vals[-1] < vals[-3] else "→"
    r.append(f"| {city} | {vals[0]:.1f} | {vals[1]:.1f} | {vals[2]:.1f} | {vals[3]:.1f} | {trend} |")

report = "\n".join(r)
with open(f"{OUTPUT}/FULL_CITY_RANKING.md", "w") as f:
    f.write(report)
print(f"报告: {len(report)}字符, {len(report.splitlines())}行")
