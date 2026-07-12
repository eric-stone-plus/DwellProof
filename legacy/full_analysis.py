#!/usr/bin/env python3
"""Archived heuristic regime report; execution and import are disabled."""

raise SystemExit(
    "DISABLED_LEGACY_FULL_ANALYSIS: arbitrary regime thresholds and city "
    "indices cannot support a property-level decision"
)

import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent

def load_all():
    """加载全部数据"""
    data = {}
    
    # 42城房价
    df = pd.read_csv(f"{OUTPUT_DIR}/70city_full.csv")
    df['日期'] = pd.to_datetime(df['日期'])
    data['hp'] = df
    
    # 房地产景气指数
    df2 = pd.read_csv(f"{OUTPUT_DIR}/real_estate.csv")
    df2['日期_dt'] = pd.to_datetime(df2['日期'])
    data['re'] = df2
    
    # 宏观
    data['gdp'] = pd.read_csv(f"{OUTPUT_DIR}/gdp.csv")
    data['cpi'] = pd.read_csv(f"{OUTPUT_DIR}/cpi.csv")
    data['pmi'] = pd.read_csv(f"{OUTPUT_DIR}/pmi.csv")
    data['lpr'] = pd.read_csv(f"{OUTPUT_DIR}/lpr.csv")
    data['m2'] = pd.read_csv(f"{OUTPUT_DIR}/m2.csv")
    
    return data


def city_tier(city):
    if city in ['北京', '上海', '广州', '深圳']:
        return 'T1'
    elif city in ['天津', '重庆', '杭州', '南京', '武汉', '成都', '西安', '长沙', '郑州']:
        return 'T2'
    else:
        return 'T3'


def build_report(data):
    hp = data['hp']
    hp['tier'] = hp['城市'].apply(city_tier)
    
    r = []
    r.append("# 内地房价监测系统 — 全量数据分析报告")
    r.append(f"\n> QUINTE-LITE Phase 0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    r.append(f"> 数据: 42城 × {hp['日期'].nunique()}月 = {len(hp)}条记录")
    r.append(f"> 数据期: {hp['日期'].min().strftime('%Y-%m')} ~ {hp['日期'].max().strftime('%Y-%m')}")
    
    # ============ 一、最新快照 ============
    latest_date = hp['日期'].max()
    latest = hp[hp['日期'] == latest_date].copy()
    
    r.append(f"\n## 一、最新数据快照 ({latest_date.strftime('%Y-%m')})\n")
    r.append("| 梯队 | 城市 | 新房同比 | 新房环比 | 二手房同比 | 二手房环比 |")
    r.append("|------|------|---------|---------|----------|----------|")
    
    for tier in ['T1', 'T2', 'T3']:
        tier_data = latest[latest['tier'] == tier].sort_values('新建商品住宅价格指数-同比', ascending=False)
        for _, row in tier_data.iterrows():
            r.append(f"| {tier} | {row['城市']} | {row['新建商品住宅价格指数-同比']:.1f} | {row['新建商品住宅价格指数-环比']:.1f} | {row['二手住宅价格指数-同比']:.1f} | {row['二手住宅价格指数-环比']:.1f} |")
    
    # ============ 二、梯队汇总 ============
    r.append("\n## 二、梯队汇总统计\n")
    
    for tier in ['T1', 'T2', 'T3']:
        tier_data = latest[latest['tier'] == tier]
        tier_name = {'T1': '一线', 'T2': '强二线', 'T3': '二线/三线'}[tier]
        avg_new_yoy = tier_data['新建商品住宅价格指数-同比'].mean()
        avg_new_mom = tier_data['新建商品住宅价格指数-环比'].mean()
        avg_used_yoy = tier_data['二手住宅价格指数-同比'].mean()
        avg_used_mom = tier_data['二手住宅价格指数-环比'].mean()
        
        r.append(f"### {tier_name} ({len(tier_data)}城)")
        r.append(f"- 新房同比均值: **{avg_new_yoy:.1f}** | 环比均值: **{avg_new_mom:.1f}**")
        r.append(f"- 二手房同比均值: **{avg_used_yoy:.1f}** | 环比均值: **{avg_used_mom:.1f}**")
        
        # 找最强/最弱
        best_new = tier_data.loc[tier_data['新建商品住宅价格指数-同比'].idxmax()]
        worst_new = tier_data.loc[tier_data['新建商品住宅价格指数-同比'].idxmin()]
        r.append(f"- 新房最强: {best_new['城市']} ({best_new['新建商品住宅价格指数-同比']:.1f}) | 最弱: {worst_new['城市']} ({worst_new['新建商品住宅价格指数-同比']:.1f})")
    
    # ============ 三、趋势分析 ============
    r.append("\n## 三、趋势分析（近12个月）\n")
    
    for tier in ['T1', 'T2', 'T3']:
        tier_name = {'T1': '一线', 'T2': '强二线', 'T3': '二线/三线'}[tier]
        r.append(f"\n### {tier_name} 新房环比走势")
        r.append("```")
        
        tier_hp = hp[hp['tier'] == tier]
        monthly = tier_hp.groupby('日期').agg({
            '新建商品住宅价格指数-环比': 'mean',
            '二手住宅价格指数-环比': 'mean'
        }).sort_index().tail(12)
        
        for date, row in monthly.iterrows():
            new_val = row['新建商品住宅价格指数-环比']
            used_val = row['二手住宅价格指数-环比']
            new_bar = "█" * max(0, int((new_val - 99) * 20))
            used_bar = "▒" * max(0, int((used_val - 99) * 20))
            r.append(f"  {date.strftime('%Y-%m')}: 新房 {new_val:.1f} {new_bar} | 二手 {used_val:.1f} {used_bar}")
        r.append("```")
    
    # ============ 四、城市分化排名 ============
    r.append("\n## 四、城市分化排名\n")
    
    r.append("### 新房同比 TOP 10（最强势）")
    r.append("| 排名 | 城市 | 梯队 | 新房同比 | 二手房同比 |")
    r.append("|------|------|------|---------|----------|")
    top10 = latest.nlargest(10, '新建商品住宅价格指数-同比')
    for i, (_, row) in enumerate(top10.iterrows(), 1):
        r.append(f"| {i} | {row['城市']} | {row['tier']} | {row['新建商品住宅价格指数-同比']:.1f} | {row['二手住宅价格指数-同比']:.1f} |")
    
    r.append("\n### 二手房同比 BOTTOM 10（最弱势）")
    r.append("| 排名 | 城市 | 梯队 | 新房同比 | 二手房同比 |")
    r.append("|------|------|------|---------|----------|")
    bot10 = latest.nsmallest(10, '二手住宅价格指数-同比')
    for i, (_, row) in enumerate(bot10.iterrows(), 1):
        r.append(f"| {i} | {row['城市']} | {row['tier']} | {row['新建商品住宅价格指数-同比']:.1f} | {row['二手住宅价格指数-同比']:.1f} |")
    
    # ============ 五、房地产景气指数 ============
    re = data['re'].sort_values('日期_dt')
    r.append("\n## 五、房地产景气指数（国房景气指数）\n")
    r.append(f"最新值: **{re.iloc[-1]['最新值']:.2f}** ({re.iloc[-1]['日期_dt'].strftime('%Y-%m')})")
    r.append(f"近1年变动: {re.iloc[-1]['近1年涨跌幅']:.2f}%")
    r.append(f"近3年变动: {re.iloc[-1]['近3年涨跌幅']:.2f}%")
    
    r.append("\n近24个月走势:")
    r.append("```")
    for _, row in re.tail(24).iterrows():
        val = row['最新值']
        chg = row['涨跌幅']
        bar = "█" * max(0, int((val - 90) * 5))
        sign = "+" if chg > 0 else ""
        r.append(f"  {row['日期_dt'].strftime('%Y-%m')}: {val:.2f} ({sign}{chg:.2f}%) {bar}")
    r.append("```")
    
    # ============ 六、宏观环境 ============
    r.append("\n## 六、宏观环境\n")
    
    # LPR
    lpr = data['lpr'].sort_values('TRADE_DATE')
    r.append("### LPR 利率走势（近6期）")
    r.append("| 日期 | 1年LPR | 5年LPR |")
    for _, row in lpr.tail(6).iterrows():
        r.append(f"| {row['TRADE_DATE']} | {row['LPR1Y']} | {row['LPR5Y']} |")
    
    # CPI
    cpi = data['cpi']
    r.append(f"\n### CPI")
    r.append(f"最新: {cpi.iloc[-1]['今值']} (预测: {cpi.iloc[-1]['预测值']}, 前值: {cpi.iloc[-1]['前值']})")
    
    # PMI
    pmi = data['pmi'].sort_values('月份')
    r.append(f"\n### PMI")
    r.append(f"制造业: {pmi.iloc[-1]['制造业-指数']} | 非制造业: {pmi.iloc[-1]['非制造业-指数']}")
    
    # ============ 七、Regime 判定 ============
    r.append("\n## 七、市场 Regime 判定\n")
    
    # 全国平均
    latest_monthly = hp.groupby('日期').agg({
        '新建商品住宅价格指数-环比': 'mean',
        '二手住宅价格指数-环比': 'mean'
    }).sort_index()
    
    recent6 = latest_monthly.tail(6)
    avg_new_mom = recent6['新建商品住宅价格指数-环比'].mean()
    avg_used_mom = recent6['二手住宅价格指数-环比'].mean()
    
    # 按梯队
    tier_regimes = {}
    for tier in ['T1', 'T2', 'T3']:
        tier_monthly = hp[hp['tier'] == tier].groupby('日期').agg({
            '新建商品住宅价格指数-环比': 'mean',
            '二手住宅价格指数-环比': 'mean'
        }).sort_index().tail(6)
        
        t_new = tier_monthly['新建商品住宅价格指数-环比'].mean()
        t_used = tier_monthly['二手住宅价格指数-环比'].mean()
        
        if t_new > 100.2 and t_used > 100.2:
            regime = "R1 上行"
        elif t_new < 99.8 and t_used < 99.8:
            regime = "R2 下行"
        elif abs(t_new - 100) < 0.3 and abs(t_used - 100) < 0.3:
            regime = "R3 震荡筑底"
        else:
            regime = "R4 分化"
        
        tier_regimes[tier] = (regime, t_new, t_used)
    
    r.append(f"**全国均值 Regime:** 新房环比均值 {avg_new_mom:.2f}, 二手房环比均值 {avg_used_mom:.2f}")
    
    if avg_new_mom > 100.3 and avg_used_mom > 100.3:
        r.append(f"**判定: R1 — 趋势上行**")
    elif avg_new_mom < 99.7 and avg_used_mom < 99.7:
        r.append(f"**判定: R2 — 趋势下行**")
    elif abs(avg_new_mom - 100) < 0.5 and abs(avg_used_mom - 100) < 0.5:
        r.append(f"**判定: R3 — 震荡筑底**")
    else:
        r.append(f"**判定: R4 — 梯队分化**")
    
    r.append("\n| 梯队 | Regime | 新房环比 | 二手房环比 |")
    r.append("|------|--------|---------|----------|")
    for tier in ['T1', 'T2', 'T3']:
        regime, t_new, t_used = tier_regimes[tier]
        tier_name = {'T1': '一线', 'T2': '强二线', 'T3': '二线/三线'}[tier]
        r.append(f"| {tier_name} | {regime} | {t_new:.2f} | {t_used:.2f} |")
    
    # ============ 八、关键信号 ============
    r.append("\n## 八、关键信号与预警\n")
    
    # 检查哪些城市二手房同比跌幅 > 10%
    severe = latest[latest['二手住宅价格指数-同比'] < 90]
    if len(severe) > 0:
        r.append(f"### 🔴 二手房同比跌幅 > 10% 的城市 ({len(severe)}个)")
        for _, row in severe.sort_values('二手住宅价格指数-同比').iterrows():
            r.append(f"- {row['城市']} ({row['tier']}): 同比 {row['二手住宅价格指数-同比']:.1f}")
    
    # 检查哪些城市新房同比 > 100 (还在涨)
    rising = latest[latest['新建商品住宅价格指数-同比'] > 100]
    if len(rising) > 0:
        r.append(f"\n### 🟢 新房仍在同比上涨的城市 ({len(rising)}个)")
        for _, row in rising.sort_values('新建商品住宅价格指数-同比', ascending=False).iterrows():
            r.append(f"- {row['城市']} ({row['tier']}): 同比 {row['新建商品住宅价格指数-同比']:.1f}")
    
    # 环比转正信号
    turning = latest[(latest['二手住宅价格指数-环比'] > 100) & (latest['二手住宅价格指数-同比'] < 95)]
    if len(turning) > 0:
        r.append(f"\n### 🟡 二手房环比转正但同比仍跌（企稳信号） ({len(turning)}个)")
        for _, row in turning.iterrows():
            r.append(f"- {row['城市']}: 环比 {row['二手住宅价格指数-环比']:.1f}, 同比 {row['二手住宅价格指数-同比']:.1f}")
    
    return "\n".join(r)


if __name__ == "__main__":
    print("=" * 60)
    print("  内地房价监测 — 全量数据分析")
    print("=" * 60)
    
    data = load_all()
    report = build_report(data)
    
    out_path = f"{OUTPUT_DIR}/full_analysis_report.md"
    with open(out_path, "w") as f:
        f.write(report)
    
    print(f"\n报告已保存: {out_path}")
    print(f"报告长度: {len(report)} 字符 ({len(report.splitlines())} 行)")
    
    # 打印摘要
    hp = data['hp']
    latest = hp[hp['日期'] == hp['日期'].max()]
    print(f"\n=== 摘要 ===")
    print(f"最新数据月: {hp['日期'].max().strftime('%Y-%m')}")
    print(f"城市数: {hp['城市'].nunique()}")
    
    for tier in ['T1', 'T2', 'T3']:
        t = latest[latest['城市'].apply(city_tier) == tier]
        tier_name = {'T1': '一线', 'T2': '强二线', 'T3': '二线/三线'}[tier]
        print(f"{tier_name}: 新房同比 {t['新建商品住宅价格指数-同比'].mean():.1f}, 二手房同比 {t['二手住宅价格指数-同比'].mean():.1f}")
