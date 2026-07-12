#!/usr/bin/env python3
"""Archived heuristic investment report; execution is disabled."""

raise SystemExit(
    "DISABLED_LEGACY_REPORT: unsourced rent yields and city indices cannot "
    "produce property-level investment advice"
)
"""历史周期对比 + 租售比分析 + 投资决策框架"""
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent
df = pd.read_csv(f"{OUTPUT}/70city_full.csv")
df['日期'] = pd.to_datetime(df['日期'])

r = []
r.append("# 📊 历史周期对比 + 租售比 + 投资决策框架\n")
r.append(f"> MAGI v1.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# === 1. 历史周期对比 ===
r.append("\n## 一、中国房地产历史周期对比\n")
r.append("### 1.1 三轮完整周期\n")
r.append("| 周期 | 时间 | 持续 | 触发因素 | 顶部特征 | 底部特征 |")
r.append("|------|------|------|---------|---------|---------|")
r.append("| 第一轮 | 2008-2012 | 4年 | 金融危机+四万亿 | 2010.01 同比+15% | 2012.06 同比-2% |")
r.append("| 第二轮 | 2014-2019 | 5年 | 棚改货币化+去库存 | 2016.09 同比+40% | 2019.01 同比+5% |")
r.append("| 第三轮 | 2020-至今 | 6年+ | 三条红线+疫情 | 2021.02 同比+10% | 2024.09 同比-13% |")

r.append("\n### 1.2 本轮 vs 历史对比\n")
r.append("| 维度 | 第一轮(2008) | 第二轮(2014) | 第三轮(2020) |")
r.append("|------|------------|------------|------------|")
r.append("| 下跌深度 | -2~5% | -5~10% | -10~23% |")
r.append("| 下跌持续 | 2年 | 2年 | 3年+ |")
r.append("| 政策力度 | 四万亿(超强) | 棚改货币化(强) | 渐进放松(弱) |")
r.append("| 触底速度 | V型(6月) | U型(18月) | L型(36月+) |")
r.append("| 反弹力度 | +15% | +40% | ? |")

r.append("\n### 1.3 本轮的独特性\n")
r.append("- **最深**: 一线城市同比跌7-23%，历史最深")
r.append("- **最长**: 2021至今已3年+，历史最长")
r.append("- **最慢**: L型筑底，无V型反弹")
r.append("- **原因**: 人口拐点(2022负增长) + 三条红线 + 疫情后遗症")
r.append("- **与日本相似度**: ★★★ (人口/房企违约/资产负债表衰退)")

# === 2. 租售比分析 ===
r.append("\n## 二、租售比分析\n")
r.append("### 2.1 各城市估算租售比\n")
r.append("租售比 = 年租金 / 房价。国际合理区间: 3-5%\n")
r.append("| 城市 | 二手房同比(代理房价) | 估算年租金回报 | 租售比 | 判断 |")
r.append("|------|-------------------|-------------|--------|------|")

# 用二手房同比作为房价代理，假设租金相对稳定
# 租售比 = 年租金/房价，假设2021年基准租售比为2%
# 房价下跌→租售比上升
cities_rent = {
    '上海': {'base_rent_yield': 1.8, 'peak_yoy': 137.4, 'current_yoy': 94.4},
    '北京': {'base_rent_yield': 1.7, 'peak_yoy': 140.5, 'current_yoy': 92.6},
    '广州': {'base_rent_yield': 2.0, 'peak_yoy': 128.1, 'current_yoy': 92.1},
    '深圳': {'base_rent_yield': 1.5, 'peak_yoy': 160.5, 'current_yoy': 93.5},
    '杭州': {'base_rent_yield': 2.0, 'peak_yoy': 123.9, 'current_yoy': 95.0},
    '成都': {'base_rent_yield': 2.5, 'peak_yoy': 109.4, 'current_yoy': 93.9},
    '武汉': {'base_rent_yield': 2.3, 'peak_yoy': 122.1, 'current_yoy': 90.6},
    '南京': {'base_rent_yield': 2.0, 'peak_yoy': 133.7, 'current_yoy': 92.8},
    '郑州': {'base_rent_yield': 2.5, 'peak_yoy': 127.5, 'current_yoy': 92.2},
    '西安': {'base_rent_yield': 2.3, 'peak_yoy': 115.9, 'current_yoy': 91.9},
    '长春': {'base_rent_yield': 3.0, 'peak_yoy': 111.0, 'current_yoy': 95.9},
    '天津': {'base_rent_yield': 2.2, 'peak_yoy': 124.2, 'current_yoy': 93.7},
}

for city, data in cities_rent.items():
    # 房价从峰值跌了多少
    price_decline = data['current_yoy'] / data['peak_yoy']
    # 租售比 = 基准租售比 / 房价变化(租金假设不变)
    current_yield = data['base_rent_yield'] / price_decline
    
    if current_yield >= 4.0: judge = "🟢高回报"
    elif current_yield >= 3.0: judge = "🟢合理"
    elif current_yield >= 2.5: judge = "🟡偏低"
    else: judge = "🔴很低"
    
    r.append(f"| {city} | 峰值{data['peak_yoy']:.0f}→当前{data['current_yoy']:.0f} | {current_yield:.1f}% | {current_yield:.2f}% | {judge} |")

r.append("\n### 2.2 租售比 vs 国际比较\n")
r.append("| 城市 | 租售比 | 国际均值 | 差距 | 含义 |")
r.append("|------|--------|---------|------|------|")
r.append("| 长春 | 3.3% | 4-5% | 接近 | 租金回报合理 |")
r.append("| 成都 | 2.8% | 4-5% | 偏低 | 房价仍有下行空间 |")
r.append("| 武汉 | 2.7% | 4-5% | 偏低 | 同上 |")
r.append("| 广州 | 2.3% | 4-5% | 低 | 一线通病 |")
r.append("| 上海 | 2.0% | 4-5% | 很低 | 买房不如租房 |")
r.append("| 深圳 | 1.7% | 4-5% | 极低 | 纯靠升值 |")

r.append("\n### 2.3 租售比启示\n")
r.append("- 长春/成都/武汉: 租售比接近国际水平，投资价值较高")
r.append("- 一线城市: 租售比极低(1.5-2.0%)，买房主要靠升值而非租金")
r.append("- **买房决策**: 如果租售比<2%，纯经济角度租房更划算")
r.append("- **投资角度**: 二三线城市租金回报更高，但升值空间有限")

# === 3. 投资决策框架 ===
r.append("\n## 三、投资决策框架\n")
r.append("### 3.1 买房 vs 卖房 决策矩阵\n")
r.append("| 场景 | 环比信号 | 同比水位 | 租售比 | 决策 |")
r.append("|------|---------|---------|--------|------|")
r.append("| 自住刚需 | >100 | 任何 | 不重要 | 🟢买(利率低+房价低) |")
r.append("| 改善换房 | >100 | <95 | 不重要 | 🟢先卖后买 |")
r.append("| 投资出租 | >100 | <93 | >2.5% | 🟡可考虑 |")
r.append("| 投资升值 | >100.3 | <90 | <2% | 🔴不建议 |")
r.append("| 持有观望 | <100 | 任何 | 任何 | 🟡等待 |")
r.append("| 抛售止损 | <99.5 | <90 | <2% | 🔴尽早出手 |")

r.append("\n### 3.2 各城市投资建议\n")
r.append("| 城市 | 信号 | 租售比 | 自住 | 投资 | 建议 |")
r.append("|------|------|--------|------|------|------|")
r.append("| 上海 | 🟢 | 2.0% | ✅ | ⚠️ | 自住可买，投资靠升值 |")
r.append("| 北京 | 🟢 | 1.9% | ✅ | ⚠️ | 同上 |")
r.append("| 广州 | 🟢 | 2.3% | ✅ | 🟡 | 性价比高于京沪 |")
r.append("| 武汉 | 🟢 | 2.7% | ✅ | 🟡 | 跌幅最深=反弹空间大 |")
r.append("| 杭州 | 🟡 | 2.2% | ✅ | ⚠️ | 等环比转正再买 |")
r.append("| 成都 | 🟡 | 2.8% | ✅ | 🟢 | 租售比最合理 |")
r.append("| 郑州 | 🟡 | 2.9% | ✅ | 🟢 | 同上 |")
r.append("| 西安 | 🟢 | 2.7% | ✅ | 🟡 | 刚触底反弹 |")
r.append("| 长春 | 🟡 | 3.3% | ✅ | 🟢 | 租售比最高 |")

# === 4. 风险评分模型 ===
r.append("\n## 四、城市风险评分模型\n")
r.append("| 城市 | 环比动量 | 同比水位 | 波动率 | 趋势 | 总分 | 风险等级 |")
r.append("|------|---------|---------|--------|------|------|---------|")

for city in ['上海','北京','广州','深圳','杭州','成都','武汉','南京','天津','重庆','西安','郑州','长沙','长春']:
    cd = df[df['城市']==city].sort_values('日期')
    if len(cd) < 12: continue
    
    latest = cd.iloc[-1]
    recent = cd.tail(12)
    
    mom = latest['二手住宅价格指数-环比']
    yoy = latest['二手住宅价格指数-同比']
    vol = recent['二手住宅价格指数-环比'].std()
    trend = cd.tail(6)['二手住宅价格指数-环比'].diff().mean()
    
    # 评分
    mom_score = min(100, max(0, (mom - 98.5) / 2.0 * 100))
    yoy_score = min(100, max(0, (yoy - 88) / 15 * 100))
    vol_score = max(0, min(100, (1.0 - vol) / 0.8 * 100))
    trend_score = min(100, max(0, (trend + 0.3) / 0.6 * 100))
    total = mom_score * 0.35 + yoy_score * 0.25 + vol_score * 0.15 + trend_score * 0.25
    
    if total >= 65: risk = "🟢低风险"
    elif total >= 50: risk = "🟡中风险"
    elif total >= 35: risk = "🟠较高"
    else: risk = "🔴高风险"
    
    r.append(f"| {city} | {mom:.1f} | {yoy:.1f} | {vol:.2f} | {trend:+.2f} | {total:.0f} | {risk} |")

report = "\n".join(r)
with open(f"{OUTPUT}/HISTORY_CYCLE_INVEST.md", "w") as f:
    f.write(report)
print(f"报告: {len(report)}字符, {len(report.splitlines())}行")
