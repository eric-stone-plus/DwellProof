#!/usr/bin/env python3
"""Archived credit narrative; execution and import are disabled."""

raise SystemExit(
    "DISABLED_LEGACY_CREDIT_ANALYSIS: hard-coded rates and unvalidated "
    "causal claims cannot support a housing decision"
)

import pandas as pd
import numpy as np
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent

# 加载数据
hp = pd.read_csv(f"{OUTPUT}/70city_full.csv")
hp['日期'] = pd.to_datetime(hp['日期'])

credit = pd.read_csv(f"{OUTPUT}/new_credit.csv")
lpr = pd.read_csv(f"{OUTPUT}/lpr.csv")

r = []
r.append("# 💰 新增信贷与房价关联分析\n")
r.append(f"> MAGI v1.0 | 数据驱动")

# 1. 新增信贷走势
r.append("\n## 一、新增人民币贷款走势\n")
credit_sorted = credit.sort_values('月份', ascending=False)
r.append("| 月份 | 当月(亿) | 同比 | 环比 |")
r.append("|------|---------|------|------|")
for _, row in credit_sorted.head(12).iterrows():
    r.append(f"| {row['月份']} | {row['当月']:,.0f} | {row['当月-同比增长']:.1f}% | {row['当月-环比增长']:.1f}% |")

# 2. LPR走势
r.append("\n## 二、LPR利率走势\n")
lpr_sorted = lpr.sort_values('TRADE_DATE')
r.append("| 日期 | 1Y LPR | 5Y LPR | 利差 |")
r.append("|------|--------|--------|------|")
for _, row in lpr_sorted.tail(12).iterrows():
    spread = row['LPR5Y'] - row['LPR1Y']
    r.append(f"| {row['TRADE_DATE']} | {row['LPR1Y']} | {row['LPR5Y']} | {spread:.2f} |")

# 3. 综合分析
r.append("\n## 三、综合分析\n")
r.append("### 信贷与房价的关系\n")
r.append("```\n新增信贷↑ → 购房资金充裕 → 房价↑\n新增信贷↓ → 购房资金紧张 → 房价↓\nLPR↓ → 房贷成本↓ → 需求↑ → 房价↑\nLPR↑ → 房贷成本↑ → 需求↓ → 房价↓\n```\n")

r.append("### 当前状态\n")
r.append("| 指标 | 当前值 | 趋势 | 对房价影响 |")
r.append("|------|--------|------|----------|")
r.append("| LPR 5Y | 3.5% | 低位持平 | 🟢利好 |")
r.append("| 新增信贷 | 正常 | 平稳 | 🟡中性 |")
r.append("| 房贷利率 | 3.2% | 历史最低 | 🟢利好 |")
r.append("| 首付比例 | 15% | 历史最低 | 🟢利好 |")

r.append("\n### 结论\n")
r.append("- 货币政策对房价中性偏利好(LPR低+首付低)")
r.append("- 但传导效果有限(买方观望情绪浓)")
r.append("- 需要房价本身止跌的信号(上海环比转正)")
r.append("- 一线城市已出现止跌信号，二三线仍在等待")

report = "\n".join(r)
with open(f"{OUTPUT}/CREDIT_ANALYSIS.md", "w") as f:
    f.write(report)
print(f"报告: {len(report)}字符")
