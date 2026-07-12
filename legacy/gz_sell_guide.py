#!/usr/bin/env python3
"""Archived Guangzhou selling guide; execution and import are disabled."""

raise SystemExit(
    "DISABLED_LEGACY_SELL_GUIDE: city-index extrapolation cannot produce a "
    "property-level sale recommendation"
)

import pandas as pd
import numpy as np
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent
df = pd.read_csv(f"{OUTPUT}/70city_full.csv")
df['日期'] = pd.to_datetime(df['日期'])

r = []
gz = df[df['城市']=='广州'].sort_values('日期')

r.append("# 🏠 二手房市场背景 — 广州篇\n")
r.append("> 仅描述城市指数；缺少标的成交与全成本证据，不构成卖房建议。")
r.append(f"> 数据: 国家统计局70城房价指数 | {gz.iloc[-1]['日期'].strftime('%Y-%m')}最新")

# 1. 周期定位
r.append("\n## 一、广州二手房周期定位\n")
peak_yoy = gz['二手住宅价格指数-同比'].max()
peak_date = gz.loc[gz['二手住宅价格指数-同比'].idxmax(), '日期'].strftime('%Y-%m')
trough_yoy = gz['二手住宅价格指数-同比'].min()
trough_date = gz.loc[gz['二手住宅价格指数-同比'].idxmin(), '日期'].strftime('%Y-%m')
current_yoy = gz.iloc[-1]['二手住宅价格指数-同比']
current_mom = gz.iloc[-1]['二手住宅价格指数-环比']

r.append(f"| 指标 | 数值 |")
r.append(f"|------|------|")
r.append(f"| 峰值 | {peak_date} 同比{peak_yoy:.1f} |")
r.append(f"| 谷底 | {trough_date} 同比{trough_yoy:.1f} |")
r.append(f"| 当前 | {gz.iloc[-1]['日期'].strftime('%Y-%m')} 同比{current_yoy:.1f} 环比{current_mom:.1f} |")
r.append(f"| 峰值到谷底 | 跌{peak_yoy-trough_yoy:.1f}个点 |")
r.append(f"| 谷底到现在 | 回升{current_yoy-trough_yoy:.1f}个点 |")
r.append(f"| 距峰值 | 还差{peak_yoy-current_yoy:.1f}个点 |")

# 2. 近24月走势
r.append("\n## 二、近24个月逐月走势\n")
r.append("| 月份 | 同比 | 环比 | 趋势 | 市场背景 |")
r.append("|------|------|------|------|---------|")

recent = gz.tail(24)
prev_mom = None
for _, row in recent.iterrows():
    yoy = row['二手住宅价格指数-同比']
    mom = row['二手住宅价格指数-环比']
    if prev_mom is not None:
        trend = "↑" if mom > prev_mom else "↓" if mom < prev_mom else "→"
    else:
        trend = "—"
    
    if mom >= 100.0: signal = "环比不低于100"
    elif mom >= 99.5: signal = "接近持平"
    else: signal = "环比低于99.5"
    
    r.append(f"| {row['日期'].strftime('%Y-%m')} | {yoy:.1f} | {mom:.1f} | {trend} | {signal} |")
    prev_mom = mom

# 3. 一线对比
r.append("\n## 三、一线城市二手房走势对比\n")
r.append("| 月份 | 北京 | 上海 | 广州 | 深圳 | 广州排名 |")
r.append("|------|------|------|------|------|---------|")

for date in sorted(df['日期'].unique())[-12:]:
    month = pd.Timestamp(date).strftime('%Y-%m')
    vals = {}
    for city in ['北京','上海','广州','深圳']:
        cd = df[(df['城市']==city) & (df['日期']==date)]
        if len(cd) > 0:
            vals[city] = cd.iloc[0]['二手住宅价格指数-环比']
    if len(vals) == 4:
        rank = sorted(vals.items(), key=lambda x: x[1], reverse=True)
        gz_rank = next(i+1 for i, (c, v) in enumerate(rank) if c == '广州')
        r.append(f"| {month} | {vals['北京']:.1f} | {vals['上海']:.1f} | {vals['广州']:.1f} | {vals['深圳']:.1f} | #{gz_rank} |")

# 4. 同比拐点预测
r.append("\n## 四、同比拐点预测\n")
mom_above = current_mom - 100
months_to_95 = abs(95 - current_yoy) / max(abs(mom_above), 0.05)
months_to_98 = abs(98 - current_yoy) / max(abs(mom_above), 0.05)
months_to_100 = abs(100 - current_yoy) / max(abs(mom_above), 0.05)

r.append(f"| 目标同比 | 预计时间 | 条件 |")
r.append(f"|---------|---------|------|")
r.append(f"| 95 (跌5%) | {months_to_95:.0f}个月后 ≈ {(pd.Timestamp(gz.iloc[-1]['日期']) + pd.DateOffset(months=int(months_to_95))).strftime('%Y-%m')} | 环比维持{current_mom:.1f} |")
r.append(f"| 98 (跌2%) | {months_to_98:.0f}个月后 ≈ {(pd.Timestamp(gz.iloc[-1]['日期']) + pd.DateOffset(months=int(months_to_98))).strftime('%Y-%m')} | 环比维持{current_mom:.1f} |")
r.append(f"| 100 (转正) | {months_to_100:.0f}个月后 ≈ {(pd.Timestamp(gz.iloc[-1]['日期']) + pd.DateOffset(months=int(months_to_100))).strftime('%Y-%m')} | 环比维持{current_mom:.1f} |")

# 5. 季节性卖房窗口
r.append("\n## 五、季节性统计\n")
r.append("基于2015-2025广州二手房月度环比均值：\n")
r.append("| 月份 | 环比均值 | 历史描述 |")
r.append("|------|---------|---------|")
df['month'] = df['日期'].dt.month
gz_seas = df[(df['城市']=='广州') & (df['日期']>='2015-01')].groupby('month')['二手住宅价格指数-环比'].mean()
for m, val in gz_seas.items():
    if val >= 100.15: label = "历史均值较高"
    elif val >= 100.0: label = "历史均值不低于100"
    elif val >= 99.9: label = "历史均值接近100"
    else: label = "历史均值低于99.9"
    r.append(f"| {m}月 | {val:.2f} | {label} |")

# 6. 实操建议
r.append("\n## 六、证据状态\n")
r.append(f"- **市场背景**: 广州城市环比{current_mom:.1f}、同比{current_yoy:.1f}")
r.append("- **决策状态**: 证据不足；未接入具体小区成交、挂牌、产权、税费、持有成本与替代方案")

# 7. 领先指标监控
r.append("\n## 七、卖房监控指标\n")
r.append("每天/每周关注这些信号：\n")
r.append("| 指标 | 来源 | 看什么 |")
r.append("|------|------|--------|")
r.append("| 上海二手房环比 | 统计局月度 | 探索性相关假设，未经样本外验证 |")
r.append("| 广州二手房成交量 | 阳光家缘 | 量在价先，放量=底部确认 |")
r.append("| 同小区挂牌量 | 贝壳/链家 | 挂牌量下降=供给收缩=利好 |")
r.append("| 带看量 | 贝壳/链家 | 带看量上升=需求回暖 |")
r.append("| LPR 5Y | 央行月度 | 下降=房贷成本降低=利好 |")
r.append("| 首套房贷利率 | 银行 | 低于3.5%=刺激需求 |")

r.append(f"\n---\n*生成时间: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')} | 数据源: 国家统计局70城房价指数*")

report = "\n".join(r)
with open(f"{OUTPUT}/GUANGZHOU_SELL_GUIDE.md", "w") as f:
    f.write(report)
print(f"报告已保存: {OUTPUT}/GUANGZHOU_SELL_GUIDE.md")
print(f"大小: {len(report)}字符, {len(report.splitlines())}行")
