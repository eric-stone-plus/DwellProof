#!/usr/bin/env python3
"""Archived market-timing model; execution and import are disabled."""

raise SystemExit(
    "DISABLED_LEGACY_MARKET_TIMING: exploratory correlations and thresholds "
    "are not validated transaction-timing evidence"
)

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

from analysis_utils import best_lag_correlation

OUTPUT = Path(__file__).resolve().parent
df = pd.read_csv(OUTPUT / "70city_full.csv")
df['日期'] = pd.to_datetime(df['日期'])

r = []
r.append("# 📊 跨城市联动模型 + 市场择时信号\n")
r.append(f"> MAGI v1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
r.append(f"> 数据: {df['城市'].nunique()}城 × {len(df)}条")

# === 1. 跨城市相关性矩阵 ===
r.append("\n## 一、跨城市二手房同比相关性矩阵\n")
cities = ['北京','上海','广州','深圳','杭州','成都','武汉','南京','天津','重庆','西安','郑州','长沙']
available = [c for c in cities if c in df['城市'].values]
pivot = df.pivot_table(index='日期', columns='城市', values='二手住宅价格指数-同比')
sub = pivot[available].dropna()
corr = sub.corr()

r.append("```")
r.append(f"{'':>6}", )
header = f"{'':>6}" + "".join(f"{c:>6}" for c in available)
r.append(header)
for c1 in available:
    row = f"{c1:>6}"
    for c2 in available:
        v = corr.loc[c1, c2]
        row += f"{v:>6.2f}"
    r.append(row)
r.append("```")

# === 2. 领先滞后关系 ===
r.append("\n## 二、领先滞后关系（上海为基准）\n")
r.append("| 领先城市 | 滞后城市 | 领先月数 | 相关系数 | 含义 |")
r.append("|---------|---------|---------|---------|------|")

sh = sub['上海'].values
lag_results = []
for city in available:
    if city == '上海': continue
    other = sub[city].values
    best_lag, best_corr = best_lag_correlation(sh, other)
    
    if best_lag > 0:
        meaning = f"探索性相关在+{best_lag}月最大（不可预测）"
    elif best_lag < 0:
        meaning = f"探索性相关在{best_lag}月最大（不可预测）"
    else:
        meaning = "同步"
    
    lag_results.append((city, best_lag, best_corr, meaning))
    r.append(f"| 上海 | {city} | {best_lag:+d}月 | {best_corr:.3f} | {meaning} |")

# === 3. 城市集群 ===
r.append("\n## 三、城市集群（走势同步的城市组）\n")

# 简单聚类：相关性>0.8的归为一组
clusters = {}
assigned = set()
for c1 in available:
    if c1 in assigned: continue
    cluster = [c1]
    assigned.add(c1)
    for c2 in available:
        if c2 in assigned: continue
        if corr.loc[c1, c2] > 0.8:
            cluster.append(c2)
            assigned.add(c2)
    if len(cluster) > 1:
        clusters[c1] = cluster

for name, members in clusters.items():
    r.append(f"- **{name}集群**: {', '.join(members)}")

# === 4. 市场择时信号系统 ===
r.append("\n## 四、市场择时信号系统\n")
r.append("### 4.1 信号定义\n")
r.append("| 信号 | 条件 | 含义 | 动作 |")
r.append("|------|------|------|------|")
r.append("| 市场回暖背景 | 上海环比>100 连续2月 + 全国环比均值>99.9 | 待验证的城市背景 | 不产生标的交易动作 |")
r.append("| 接近100背景 | 上海环比100附近(99.8-100.2) | 城市指数描述 | 不产生标的交易动作 |")
r.append("| 市场下行背景 | 上海环比<99.5 连续3月 + 全国环比均值<99.8 | 待验证的城市背景 | 不产生标的交易动作 |")
r.append("| 极端下行背景 | 上海环比<99.0 + 同比加速下跌 | 风险核查触发器 | 核验标的级证据 |")

r.append("\n### 4.2 当前信号\n")
sh_latest = df[df['城市']=='上海'].sort_values('日期').tail(6)
sh_mom = sh_latest['二手住宅价格指数-环比'].values
national_mom = df.groupby('日期')['二手住宅价格指数-环比'].mean().sort_index().tail(6).values

r.append(f"上海近6月环比: {', '.join(f'{v:.1f}' for v in sh_mom)}")
r.append(f"全国近6月环比均值: {', '.join(f'{v:.2f}' for v in national_mom)}")

if sh_mom[-1] >= 100.0 and sh_mom[-2] >= 100.0:
    signal = "ℹ️市场回暖背景（不构成买入建议）"
elif sh_mom[-1] >= 99.8:
    signal = "ℹ️城市指数接近100（不构成交易建议）"
elif sh_mom[-1] < 99.5:
    signal = "ℹ️市场下行背景（不构成卖出建议）"
else:
    signal = "ℹ️城市指数背景（不构成交易建议）"
r.append(f"\n**当前信号: {signal}**")

r.append("\n### 4.3 旧信号回测状态\n")
r.append("**已停用：城市指数后续均值不是标的投资净收益，不能用于证明买卖建议准确。**")

# === 5. 各城市择时信号 ===
r.append("\n## 五、各城市当前择时信号\n")
r.append("| 城市 | 当前环比 | 近3月趋势 | 信号 | 建议 |")
r.append("|------|---------|----------|------|------|")

for city in available:
    cd = df[df['城市']==city].sort_values('日期').tail(6)
    mom_vals = cd['二手住宅价格指数-环比'].values
    if len(mom_vals) < 3: continue
    
    current = mom_vals[-1]
    trend = mom_vals[-1] - mom_vals[-3]
    
    if current >= 100.3 and trend > 0:
        sig = "ℹ️回暖背景"
        advice = "需核验标的级证据"
    elif current >= 100.0:
        sig = "ℹ️回暖背景"
        advice = "不构成买入建议"
    elif current >= 99.8 and trend > 0.2:
        sig = "指数变化背景"
        advice = "需核验标的级证据"
    elif current >= 99.8:
        sig = "指数接近100"
        advice = "不产生交易动作"
    elif current >= 99.5 and trend > 0:
        sig = "指数变化背景"
        advice = "不产生交易动作"
    elif current < 99.5:
        sig = "指数低于99.5"
        advice = "不构成回避建议"
    else:
        sig = "城市指数背景"
        advice = "不产生交易动作"
    
    r.append(f"| {city} | {current:.1f} | {trend:+.1f} | {sig} | {advice} |")

report = "\n".join(r)
with open(OUTPUT / "MARKET_TIMING_MODEL.md", "w", encoding="utf-8") as f:
    f.write(report)
print(f"报告: {OUTPUT / 'MARKET_TIMING_MODEL.md'}")
print(f"大小: {len(report)}字符, {len(report.splitlines())}行")
