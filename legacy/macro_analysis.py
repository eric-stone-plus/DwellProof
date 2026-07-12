#!/usr/bin/env python3
"""Archived macro narrative; execution and import are disabled."""

raise SystemExit(
    "DISABLED_LEGACY_MACRO_ANALYSIS: hard-coded macro values and causal "
    "claims cannot support a housing decision"
)

import pandas as pd
import numpy as np
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent

# 加载数据
hp = pd.read_csv(OUTPUT / "70city_full.csv")
hp['日期'] = pd.to_datetime(hp['日期'])

lpr = pd.read_csv(OUTPUT / "lpr.csv")
pmi = pd.read_csv(OUTPUT / "pmi.csv")
cpi = pd.read_csv(OUTPUT / "cpi.csv")
m2 = pd.read_csv(OUTPUT / "m2.csv")

r = []
r.append("# 📊 宏观经济指标与房价关联分析\n")
r.append(f"> MAGI v1.0 | 数据驱动")

# 全国二手房环比均值
national_mom = hp.groupby('日期')['二手住宅价格指数-环比'].mean().sort_index()

# 1. LPR分析
r.append("\n## 一、LPR利率走势\n")
lpr_sorted = lpr.sort_values('TRADE_DATE')
r.append("| 日期 | 1Y LPR | 5Y LPR | 利差 |")
r.append("|------|--------|--------|------|")
for _, row in lpr_sorted.tail(12).iterrows():
    spread = row['LPR5Y'] - row['LPR1Y']
    r.append(f"| {row['TRADE_DATE']} | {row['LPR1Y']} | {row['LPR5Y']} | {spread:.2f} |")

# 2. PMI分析
r.append("\n## 二、PMI走势\n")
pmi_sorted = pmi.sort_values('月份')
r.append("| 月份 | 制造业 | 非制造业 | 制造业趋势 |")
r.append("|------|--------|---------|----------|")
prev_pmi = None
for _, row in pmi_sorted.tail(12).iterrows():
    mfg = row['制造业-指数']
    non_mfg = row['非制造业-指数']
    if prev_pmi is not None:
        trend = "↑" if mfg > prev_pmi else "↓" if mfg < prev_pmi else "→"
    else:
        trend = "—"
    r.append(f"| {row['月份']} | {mfg} | {non_mfg} | {trend} |")
    prev_pmi = mfg

# 3. M2分析
r.append("\n## 三、M2货币供应\n")
m2_sorted = m2.sort_values('日期')
r.append("| 日期 | M2(亿) | 同比 | 趋势 |")
r.append("|------|--------|------|------|")
prev_m2 = None
for _, row in m2_sorted.tail(12).iterrows():
    val = row['今值']
    yoy = row['预测值'] if pd.notna(row['预测值']) else row['前值']
    if prev_m2 is not None:
        trend = "↑" if val > prev_m2 else "↓" if val < prev_m2 else "→"
    else:
        trend = "—"
    r.append(f"| {row['日期']} | {val} | {yoy} | {trend} |")
    prev_m2 = val

# 4. CPI分析
r.append("\n## 四、CPI走势\n")
cpi_sorted = cpi.sort_values('日期')
r.append("| 日期 | CPI | 预测 | 前值 |")
r.append("|------|-----|------|------|")
for _, row in cpi_sorted.tail(12).iterrows():
    r.append(f"| {row['日期']} | {row['今值']} | {row['预测值']} | {row['前值']} |")

# 5. 综合分析
r.append("\n## 五、综合分析\n")
r.append("### 宏观环境对房价的影响\n")
r.append("| 指标 | 当前值 | 趋势 | 对房价影响 |")
r.append("|------|--------|------|----------|")
latest_lpr = lpr_sorted.dropna(subset=['LPR5Y']).iloc[-1]
latest_pmi = pmi_sorted.iloc[-1]
mfg = float(latest_pmi['制造业-指数'])
non_mfg = float(latest_pmi['非制造业-指数'])
mfg_state = "扩张" if mfg > 50 else "临界" if mfg == 50 else "收缩"
non_mfg_state = "扩张" if non_mfg > 50 else "临界" if non_mfg == 50 else "收缩"
r.append(f"| LPR 5Y | {latest_lpr['LPR5Y']}% ({latest_lpr['TRADE_DATE']}) | 最新可用值 | 仅成本背景 |")
r.append(f"| 制造业PMI | {mfg:.1f} ({latest_pmi['月份']}) | {mfg_state} | 仅宏观背景 |")
r.append(f"| 非制造业PMI | {non_mfg:.1f} ({latest_pmi['月份']}) | {non_mfg_state} | 仅宏观背景 |")
r.append("| CPI | ~0% | 低迷 | 🟡中性(低通胀) |")
r.append("| M2增速 | ~7% | 平稳 | 🟡中性(流动性适度) |")

r.append("\n### 宏观环境总结\n")
r.append("- **货币政策**: LPR 3.5%历史最低，但传导效果有限")
r.append(f"- **经济景气**: 最新制造业PMI为{mfg:.1f}、非制造业PMI为{non_mfg:.1f}，均需结合观察期解释")
r.append("- **通胀**: CPI低迷，实际利率偏高")
r.append("- **流动性**: M2增速7%，适度宽松")
r.append("- **综合**: 宏观环境对房价中性偏利好，但不足以推动V型反弹")

report = "\n".join(r)
with open(OUTPUT / "MACRO_ANALYSIS.md", "w", encoding="utf-8") as f:
    f.write(report)
print(f"报告: {len(report)}字符")
