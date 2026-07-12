#!/usr/bin/env python3
"""Archived heuristic analysis pipeline; execution and import are disabled."""

raise SystemExit(
    "DISABLED_LEGACY_DATA_ANALYSIS: arbitrary regime thresholds and stale "
    "macro inputs cannot support a property-level decision"
)

import pandas as pd
import numpy as np
from datetime import datetime
import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent

def load_data():
    """加载所有数据源"""
    data = {}
    
    # 70城新房+二手房价格指数
    df = pd.read_csv(f"{OUTPUT_DIR}/70city_new_house.csv")
    df['日期'] = pd.to_datetime(df['日期'])
    data['house_price'] = df
    print(f"70城房价: {len(df)} 行, {df['日期'].min()} ~ {df['日期'].max()}")
    print(f"  城市: {df['城市'].nunique()} 个 ({', '.join(df['城市'].unique()[:8])}...)")
    
    # 房地产景气指数
    df2 = pd.read_csv(f"{OUTPUT_DIR}/real_estate.csv")
    df2['日期'] = pd.to_datetime(df2['日期'])
    data['real_estate'] = df2
    print(f"房地产景气指数: {len(df2)} 行, {df2['日期'].min()} ~ {df2['日期'].max()}")
    
    # GDP
    df3 = pd.read_csv(f"{OUTPUT_DIR}/gdp.csv")
    data['gdp'] = df3
    print(f"GDP: {len(df3)} 行")
    
    # CPI
    df4 = pd.read_csv(f"{OUTPUT_DIR}/cpi.csv")
    data['cpi'] = df4
    print(f"CPI: {len(df4)} 行")
    
    # PMI
    df5 = pd.read_csv(f"{OUTPUT_DIR}/pmi.csv")
    data['pmi'] = df5
    print(f"PMI: {len(df5)} 行")
    
    # LPR
    df6 = pd.read_csv(f"{OUTPUT_DIR}/lpr.csv")
    data['lpr'] = df6
    print(f"LPR: {len(df6)} 行")
    
    # M2
    df7 = pd.read_csv(f"{OUTPUT_DIR}/m2.csv")
    data['m2'] = df7
    print(f"M2: {len(df7)} 行")
    
    return data


def analyze_trends(data):
    """趋势分析"""
    df = data['house_price']
    
    report = []
    report.append("# 内地70城房价数据全景分析\n")
    report.append(f"> 数据期: {df['日期'].min().strftime('%Y-%m')} ~ {df['日期'].max().strftime('%Y-%m')}\n")
    
    # 1. 最新数据概览
    latest = df[df['日期'] == df['日期'].max()]
    report.append("\n## 一、最新数据快照\n")
    report.append(f"最新月份: {df['日期'].max().strftime('%Y-%m')}\n")
    report.append(f"| 城市 | 新房同比 | 新房环比 | 二手房同比 | 二手房环比 |")
    report.append(f"|------|---------|---------|----------|----------|")
    for _, row in latest.iterrows():
        report.append(f"| {row['城市']} | {row['新建商品住宅价格指数-同比']:.1f} | {row['新建商品住宅价格指数-环比']:.1f} | {row['二手住宅价格指数-同比']:.1f} | {row['二手住宅价格指数-环比']:.1f} |")
    
    # 2. 趋势分析 - 分城市梯队
    report.append("\n## 二、城市梯队分析\n")
    
    tier1 = ['北京', '上海', '广州', '深圳']
    tier2 = ['天津', '重庆', '杭州', '南京', '武汉', '成都', '西安', '长沙']
    
    for tier_name, cities in [("一线城市", tier1), ("强二线城市", tier2)]:
        report.append(f"\n### {tier_name}\n")
        for city in cities:
            city_data = df[df['城市'] == city].sort_values('日期')
            if len(city_data) < 2:
                continue
            
            # 最新值
            latest_row = city_data.iloc[-1]
            
            # 计算趋势
            recent = city_data.tail(6)  # 最近6个月
            if len(recent) >= 3:
                new_trend = recent['新建商品住宅价格指数-环比'].values
                used_trend = recent['二手住宅价格指数-环比'].values
                
                new_direction = "↑" if new_trend[-1] > 100 else "↓" if new_trend[-1] < 100 else "→"
                used_direction = "↑" if used_trend[-1] > 100 else "↓" if used_trend[-1] < 100 else "→"
                
                report.append(f"- **{city}**: 新房同比 {latest_row['新建商品住宅价格指数-同比']:.1f} {new_direction} | 二手房同比 {latest_row['二手住宅价格指数-同比']:.1f} {used_direction}")
    
    # 3. 全国趋势
    report.append("\n## 三、全国趋势判断\n")
    
    # 按月汇总（取均值）
    monthly = df.groupby('日期').agg({
        '新建商品住宅价格指数-同比': 'mean',
        '新建商品住宅价格指数-环比': 'mean',
        '二手住宅价格指数-同比': 'mean',
        '二手住宅价格指数-环比': 'mean'
    }).sort_index()
    
    latest_month = monthly.iloc[-1]
    prev_month = monthly.iloc[-2] if len(monthly) > 1 else latest_month
    
    report.append(f"| 指标 | 最新月均值 | 上月均值 | 变化 |")
    report.append(f"|------|----------|---------|------|")
    for col in monthly.columns:
        direction = "↑" if latest_month[col] > prev_month[col] else "↓"
        report.append(f"| {col} | {latest_month[col]:.2f} | {prev_month[col]:.2f} | {direction} |")
    
    # 4. 房地产景气指数趋势
    re = data['real_estate'].sort_values('日期')
    report.append("\n## 四、房地产景气指数\n")
    last_date = pd.to_datetime(re.iloc[-1]['日期'])
    report.append(f"最新值: {re.iloc[-1]['最新值']:.2f} ({last_date.strftime('%Y-%m')})")
    report.append(f"近1年涨跌: {re.iloc[-1]['近1年涨跌幅']:.2f}%")
    report.append(f"近3年涨跌: {re.iloc[-1]['近3年涨跌幅']:.2f}%")
    
    # 最近12个月趋势
    recent_re = re.tail(12)
    report.append(f"\n近12个月趋势:")
    for _, row in recent_re.iterrows():
        d = pd.to_datetime(row['日期'])
        bar = "█" * max(1, int(abs(row['涨跌幅']) * 10)) if pd.notna(row['涨跌幅']) else ""
        sign = "+" if pd.notna(row['涨跌幅']) and row['涨跌幅'] > 0 else ""
        report.append(f"  {d.strftime('%Y-%m')}: {row['最新值']:.2f} ({sign}{row['涨跌幅']:.2f}%) {bar}")
    
    return "\n".join(report)


def analyze_macro_context(data):
    """宏观环境分析"""
    report = []
    report.append("\n## 五、宏观环境\n")
    
    # LPR
    lpr = data['lpr'].sort_values('TRADE_DATE')
    report.append(f"\n### LPR 利率")
    recent_lpr = lpr.tail(5)
    for _, row in recent_lpr.iterrows():
        report.append(f"- {row['TRADE_DATE']}: 1Y={row['LPR1Y']}, 5Y={row['LPR5Y']}")
    
    # CPI
    cpi = data['cpi']
    if len(cpi) > 0:
        latest_cpi = cpi.iloc[-1] if len(cpi) > 0 else None
        report.append(f"\n### CPI")
        report.append(f"最新: {latest_cpi['今值']} (预测: {latest_cpi['预测值']}, 前值: {latest_cpi['前值']})")
    
    # PMI
    pmi = data['pmi']
    if len(pmi) > 0:
        latest_pmi = pmi.sort_values('月份').iloc[-1]
        report.append(f"\n### PMI")
        report.append(f"最新制造业PMI: {latest_pmi['制造业-指数']}")
        report.append(f"最新非制造业PMI: {latest_pmi['非制造业-指数']}")
    
    return "\n".join(report)


def compute_regime(df):
    """Regime 识别"""
    monthly = df.groupby('日期').agg({
        '新建商品住宅价格指数-环比': 'mean',
        '二手住宅价格指数-环比': 'mean'
    }).sort_index()
    
    # 最近6个月均值
    recent = monthly.tail(6)
    avg_mom_new = recent['新建商品住宅价格指数-环比'].mean()
    avg_mom_used = recent['二手住宅住宅价格指数-环比'].mean() if '二手住宅住宅价格指数-环比' in recent.columns else recent['二手住宅价格指数-环比'].mean()
    
    # Regime 判定
    if avg_mom_new > 100.5 and avg_mom_used > 100.5:
        regime = "R1 — 趋势上行"
    elif avg_mom_new < 99.5 and avg_mom_used < 99.5:
        regime = "R2 — 趋势下行"
    elif abs(avg_mom_new - 100) < 0.5 and abs(avg_mom_used - 100) < 0.5:
        regime = "R3 — 震荡筑底"
    else:
        regime = "R4 — 分化（新房vs二手/一线vs二线）"
    
    return regime, avg_mom_new, avg_mom_used


def generate_full_report(data):
    """生成完整分析报告"""
    report = []
    report.append("# 内地房价监测系统 — 数据分析报告")
    report.append(f"\n> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append(f"> 数据源: 国家统计局70城房价指数 + 宏观经济指标")
    
    # 趋势分析
    report.append(analyze_trends(data))
    
    # 宏观环境
    report.append(analyze_macro_context(data))
    
    # Regime 判定
    regime, avg_new, avg_used = compute_regime(data['house_price'])
    report.append(f"\n## 六、市场 Regime 判定\n")
    report.append(f"**当前 Regime: {regime}**\n")
    report.append(f"- 新房近6月环比均值: {avg_new:.2f}")
    report.append(f"- 二手房近6月环比均值: {avg_used:.2f}")
    
    return "\n".join(report)


if __name__ == "__main__":
    print("=" * 60)
    print("  内地房价监测系统 — 数据分析管线")
    print("=" * 60)
    
    data = load_data()
    report = generate_full_report(data)
    
    with open(f"{OUTPUT_DIR}/data_analysis_report.md", "w") as f:
        f.write(report)
    
    print(f"\n报告已保存: {OUTPUT_DIR}/data_analysis_report.md")
    print(f"报告长度: {len(report)} 字符")
