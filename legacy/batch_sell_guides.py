#!/usr/bin/env python3
"""Archived batch selling guides; execution and import are disabled."""

raise SystemExit(
    "DISABLED_LEGACY_BATCH_SELL_GUIDES: unverified web data and city-index "
    "extrapolation cannot produce property-level sale recommendations"
)

import pandas as pd
import numpy as np
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent
df = pd.read_csv(f"{OUTPUT}/70city_full.csv")
df['日期'] = pd.to_datetime(df['日期'])

CITIES = ['珠海', '长春', '上海', '北京', '武汉', '杭州', '成都', '郑州', '西安']

# 珠海不在70城标准中，用akshare单独拉
import akshare as ak
try:
    zh = ak.macro_china_new_house_price(city_first="珠海", city_second="珠海")
    zh['城市'] = '珠海'
    zh['日期'] = pd.to_datetime(zh['日期'])
    df = pd.concat([df, zh], ignore_index=True)
    print(f"珠海数据已补充: {len(zh)}行")
except:
    print("珠海数据拉取失败，跳过")

def gen_city_report(city, df):
    cd = df[df['城市']==city].sort_values('日期')
    if len(cd) < 24:
        return f"# {city} 市场背景数据不足\n"
    
    r = []
    r.append(f"# 🏠 二手房市场背景 — {city}篇\n")
    r.append("> 本报告仅描述城市指数，缺少标的成交与成本证据，不构成卖房建议。")
    r.append(f"> 数据: 国家统计局70城房价指数 | {cd.iloc[-1]['日期'].strftime('%Y-%m')}最新")
    
    # 1. 周期定位
    r.append(f"\n## 一、{city}二手房周期定位\n")
    peak_yoy = cd['二手住宅价格指数-同比'].max()
    peak_date = cd.loc[cd['二手住宅价格指数-同比'].idxmax(), '日期'].strftime('%Y-%m')
    trough_yoy = cd['二手住宅价格指数-同比'].min()
    trough_date = cd.loc[cd['二手住宅价格指数-同比'].idxmin(), '日期'].strftime('%Y-%m')
    current_yoy = cd.iloc[-1]['二手住宅价格指数-同比']
    current_mom = cd.iloc[-1]['二手住宅价格指数-环比']
    
    r.append(f"| 指标 | 数值 |")
    r.append(f"|------|------|")
    r.append(f"| 峰值 | {peak_date} 同比{peak_yoy:.1f} |")
    r.append(f"| 谷底 | {trough_date} 同比{trough_yoy:.1f} |")
    r.append(f"| 当前 | {cd.iloc[-1]['日期'].strftime('%Y-%m')} 同比{current_yoy:.1f} 环比{current_mom:.1f} |")
    r.append(f"| 峰值到谷底 | 跌{peak_yoy-trough_yoy:.1f}个点 |")
    r.append(f"| 谷底到现在 | 回升{current_yoy-trough_yoy:.1f}个点 |")
    r.append(f"| 距峰值 | 还差{peak_yoy-current_yoy:.1f}个点 |")
    
    # 2. 近18个月走势
    r.append(f"\n## 二、近18个月走势\n")
    r.append("| 月份 | 同比 | 环比 | 趋势 | 市场背景 |")
    r.append("|------|------|------|------|---------|")
    
    recent = cd.tail(18)
    prev_mom = None
    for _, row in recent.iterrows():
        yoy = row['二手住宅价格指数-同比']
        mom = row['二手住宅价格指数-环比']
        if pd.isna(mom):
            continue
        trend = "↑" if prev_mom and mom > prev_mom else "↓" if prev_mom and mom < prev_mom else "→" if prev_mom else "—"
        if mom >= 100.0: signal = "环比不低于100"
        elif mom >= 99.5: signal = "接近持平"
        else: signal = "环比低于99.5"
        r.append(f"| {row['日期'].strftime('%Y-%m')} | {yoy:.1f} | {mom:.1f} | {trend} | {signal} |")
        prev_mom = mom
    
    # 3. 同比拐点预测
    r.append(f"\n## 三、同比拐点预测\n")
    mom_above = current_mom - 100
    if abs(mom_above) < 0.01:
        r.append(f"环比恰好100.0，同比维持当前水平，需环比持续>100才能改善\n")
    else:
        months_95 = abs(95 - current_yoy) / max(abs(mom_above), 0.05)
        months_98 = abs(98 - current_yoy) / max(abs(mom_above), 0.05)
        months_100 = abs(100 - current_yoy) / max(abs(mom_above), 0.05)
        last_date = cd.iloc[-1]['日期']
        r.append(f"| 目标 | 预计时间 | 条件 |")
        r.append(f"|------|---------|------|")
        r.append(f"| 95 (跌5%) | {int(months_95)}月后 ≈ {(pd.Timestamp(last_date)+pd.DateOffset(months=int(months_95))).strftime('%Y-%m')} | 环比维持{current_mom:.1f} |")
        r.append(f"| 98 (跌2%) | {int(months_98)}月后 ≈ {(pd.Timestamp(last_date)+pd.DateOffset(months=int(months_98))).strftime('%Y-%m')} | 环比维持{current_mom:.1f} |")
        r.append(f"| 100 (转正) | {int(months_100)}月后 ≈ {(pd.Timestamp(last_date)+pd.DateOffset(months=int(months_100))).strftime('%Y-%m')} | 环比维持{current_mom:.1f} |")
    
    # 4. 季节性
    r.append(f"\n## 四、季节性统计\n")
    df_c = df[(df['城市']==city) & (df['日期']>='2015-01')].copy()
    df_c['month'] = df_c['日期'].dt.month
    seas = df_c.groupby('month')['二手住宅价格指数-环比'].mean()
    r.append("| 月份 | 环比均值 | 描述 |")
    r.append("|------|---------|------|")
    for m, val in seas.items():
        if pd.isna(val): continue
        if val >= 100.2: label = "历史均值较高"
        elif val >= 100.0: label = "历史均值不低于100"
        elif val >= 99.9: label = "历史均值接近100"
        else: label = "历史均值低于99.9"
        r.append(f"| {m}月 | {val:.2f} | {label} |")
    
    # 5. Evidence gate
    r.append(f"\n## 五、证据状态\n")
    r.append(f"- **市场背景**: 城市环比指数{current_mom:.1f}")
    r.append(f"- **同比水位**: {current_yoy:.1f}（比去年跌{100-current_yoy:.1f}%）")
    r.append("- **决策状态**: 证据不足；需补充同小区真实成交、挂牌竞争、持有成本、税费和替代方案")
    
    # 6. 监控指标
    r.append(f"\n## 六、监控指标\n")
    r.append(f"| 指标 | 看什么 |")
    r.append(f"|------|--------|")
    r.append(f"| 上海二手环比 | 探索性相关假设，未经样本外验证 |")
    r.append(f"| {city}二手成交量 | 量在价先，放量=底部确认 |")
    r.append(f"| 同小区挂牌量 | 挂牌量下降=供给收缩=利好 |")
    r.append(f"| LPR 5Y | 下降=房贷成本降低=利好 |")
    
    r.append(f"\n---\n*QUINTE-LITE | {pd.Timestamp.now().strftime('%Y-%m-%d')}*")
    return "\n".join(r)


# 批量生成
for city in CITIES:
    print(f"生成 {city}...", end="", flush=True)
    report = gen_city_report(city, df)
    fname = f"SELL_GUIDE_{city}.md"
    with open(f"{OUTPUT}/{fname}", "w") as f:
        f.write(report)
    print(f" ✅ {len(report)}字符 → {fname}")

print(f"\n全部完成: {len(CITIES)}城")
