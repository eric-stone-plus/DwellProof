#!/usr/bin/env python3
"""
地产中介分析系统 — 全量版
63城 × 184月 × 多维度分析
"""

import pandas as pd
import numpy as np
import glob
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parent

# === 数据加载 ===
def load_all():
    main = pd.read_csv(OUTPUT_DIR / "70city_full.csv")
    main['日期'] = pd.to_datetime(main['日期'])
    
    extras = []
    for f in OUTPUT_DIR.glob("city_*.csv"):
        try:
            df = pd.read_csv(f)
            df['日期'] = pd.to_datetime(df['日期'])
            extras.append(df)
        except (OSError, ValueError, KeyError) as exc:
            print(f"跳过无效扩展数据 {f.name}: {exc}")
    
    all_df = pd.concat([main] + extras, ignore_index=True)
    # The monitored main dataset is canonical when an extra file overlaps it.
    all_df = all_df.drop_duplicates(subset=['城市', '日期'], keep='first')
    all_df = all_df.sort_values(['城市', '日期']).reset_index(drop=True)
    all_df['梯队'] = all_df['城市'].apply(tier)
    all_df['区域'] = all_df['城市'].map(REGION_MAP).fillna('其他')
    return all_df

def tier(city):
    if city in ['北京','上海','广州','深圳']: return 'T1'
    if city in ['天津','重庆','杭州','南京','武汉','成都','西安','长沙','郑州']: return 'T2'
    return 'T3'

REGION_MAP = {
    '北京': '京津冀', '天津': '京津冀', '唐山': '京津冀', '石家庄': '京津冀',
    '上海': '长三角', '南京': '长三角', '杭州': '长三角', '合肥': '长三角',
    '苏州': '长三角', '无锡': '长三角', '宁波': '长三角', '温州': '长三角',
    '金华': '长三角', '扬州': '长三角', '徐州': '长三角', '安庆': '长三角', '蚌埠': '长三角',
    '广州': '珠三角', '深圳': '珠三角', '惠州': '珠三角', '韶关': '珠三角', '湛江': '珠三角',
    '武汉': '华中', '长沙': '华中', '郑州': '华中', '南昌': '华中',
    '洛阳': '华中', '岳阳': '华中', '宜昌': '华中', '常德': '华中', '平顶山': '华中', '九江': '华中',
    '成都': '西南', '重庆': '西南', '贵阳': '西南', '昆明': '西南',
    '遵义': '西南', '泸州': '西南', '南充': '西南', '大理': '西南',
    '西安': '西北', '银川': '西北', '西宁': '西北', '乌鲁木齐': '西北', '包头': '西北', '呼和浩特': '内蒙',
    '沈阳': '东北', '大连': '东北', '长春': '东北', '哈尔滨': '东北', '牡丹江': '东北',
    '济南': '山东', '青岛': '山东', '烟台': '山东',
    '福州': '福建', '厦门': '福建', '泉州': '福建',
    '南宁': '广西', '桂林': '广西', '北海': '广西',
    '海口': '海南', '三亚': '海南', '赣州': '江西', '太原': '山西',
}

# === 核心分析 ===
def build_mega_report(df):
    raise RuntimeError(
        "DISABLED_LEGACY_MEGA_REPORT: heuristic regime, timing, and ranking "
        "labels are not validated property-level evidence"
    )

    latest = df[df['日期'] == df['日期'].max()]
    r = []
    r.append(f"# 城市价格指数背景 — 全量版")
    r.append(f"\n> {datetime.now().strftime('%Y-%m-%d %H:%M')} | {df['城市'].nunique()}城 × {len(df)}条")
    r.append(f"> QUINTE-LITE hm+cc+mc (mimo-v2.5-pro)")
    r.append("> 仅描述城市价格指数；不代表成交热度、真实需求、库存、房源估值或交易建议。")
    
    # === 1. 市场全景 ===
    r.append("\n## 一、市场全景\n")
    r.append(f"| 指标 | 数值 |")
    r.append(f"|------|------|")
    r.append(f"| 覆盖城市 | {df['城市'].nunique()}城")
    r.append(f"| 数据期 | {df['日期'].min().strftime('%Y-%m')} ~ {df['日期'].max().strftime('%Y-%m')}")
    r.append(f"| 总记录 | {len(df):,}条")
    r.append(f"| 最新月 | {latest['日期'].max().strftime('%Y-%m')}")
    
    # === 2. 梯队汇总 ===
    r.append("\n## 二、梯队汇总\n")
    r.append("| 梯队 | 城市数 | 新房环比 | 二手环比 | 新房同比 | 二手同比 | Regime |")
    r.append("|------|--------|---------|---------|---------|---------|--------|")
    
    for t in ['T1','T2','T3']:
        td = latest[latest['梯队']==t]
        if len(td)==0: continue
        name = {'T1':'一线','T2':'强二线','T3':'二三线'}[t]
        nm = td['新建商品住宅价格指数-环比'].mean()
        um = td['二手住宅价格指数-环比'].mean()
        ny = td['新建商品住宅价格指数-同比'].mean()
        uy = td['二手住宅价格指数-同比'].mean()
        regime = "R3筑底" if nm>=100 and um>=100 else "R3早期" if nm>=99.8 and um>=99.8 else "R2下行"
        r.append(f"| {name} | {len(td)} | {nm:.2f} | {um:.2f} | {ny:.1f} | {uy:.1f} | {regime} |")
    
    # === 3. 区域分析 ===
    r.append("\n## 三、区域分析\n")
    r.append("| 区域 | 城市数 | 新房环比 | 二手环比 | 二手同比 | Regime |")
    r.append("|------|--------|---------|---------|---------|--------|")
    
    for region in sorted(latest['区域'].unique()):
        rd = latest[latest['区域']==region]
        if len(rd)<1: continue
        nm = rd['新建商品住宅价格指数-环比'].mean()
        um = rd['二手住宅价格指数-环比'].mean()
        uy = rd['二手住宅价格指数-同比'].mean()
        regime = "R3" if nm>=100 and um>=100 else "R3早期" if um>=99.8 else "R2"
        r.append(f"| {region} | {len(rd)} | {nm:.2f} | {um:.2f} | {uy:.1f} | {regime} |")
    
    # === 4. 城市排名 ===
    r.append("\n## 四、城市排名\n")
    
    r.append("### 4.1 二手房环比指数数值最高 15 城（非投资排名）\n")
    r.append("| 排名 | 城市 | 梯队 | 区域 | 二手环比 | 二手同比 | 信号 |")
    r.append("|------|------|------|------|---------|---------|------|")
    for i, (_, row) in enumerate(latest.nlargest(15, '二手住宅价格指数-环比').iterrows(), 1):
        mom = row['二手住宅价格指数-环比']
        signal = "✅转正" if mom>=100 else "⚠️接近" if mom>=99.9 else "❌未到"
        r.append(f"| {i} | {row['城市']} | {row['梯队']} | {row['区域']} | {mom:.1f} | {row['二手住宅价格指数-同比']:.1f} | {signal} |")
    
    r.append("\n### 4.2 二手房同比指数数值最低 15 城（非风险排名）\n")
    r.append("| 排名 | 城市 | 梯队 | 区域 | 二手同比 | 二手环比 | 风险 |")
    r.append("|------|------|------|------|---------|---------|------|")
    for i, (_, row) in enumerate(latest.nsmallest(15, '二手住宅价格指数-同比').iterrows(), 1):
        yoy = row['二手住宅价格指数-同比']
        mom = row['二手住宅价格指数-环比']
        label = "指数低于91" if yoy<91 and mom<100 else "指数低于93" if yoy<93 else "指数背景"
        r.append(f"| {i} | {row['城市']} | {row['梯队']} | {row['区域']} | {yoy:.1f} | {mom:.1f} | {label} |")
    
    # === 5. 成交热度代理 ===
    r.append("\n## 五、新房与二手房指数差\n")
    r.append("### 5.1 环比指数差（不能推断成交量或真实需求）\n")
    r.append("| 城市 | 新房环比 | 二手环比 | 指数差 | 用途 |")
    r.append("|------|---------|---------|--------|------|")
    for _, row in latest.iterrows():
        gap = row['二手住宅价格指数-环比'] - row['新建商品住宅价格指数-环比']
    # 只显示有显著倒挂的
    for _, row in latest.sort_values('二手住宅价格指数-环比', ascending=False).iterrows():
        gap = row['二手住宅价格指数-环比'] - row['新建商品住宅价格指数-环比']
        if abs(gap) > 0.2:
            r.append(f"| {row['城市']} | {row['新建商品住宅价格指数-环比']:.1f} | {row['二手住宅价格指数-环比']:.1f} | {gap:+.1f} | 城市指数背景 |")
    
    r.append("\n### 5.2 环比指数波动率（不能替代成交量）\n")
    r.append("以下只描述指数波动，不能据此推断成交活跃度。\n")
    r.append("| 城市 | 梯队 | 二手环比波动 | 新房环比波动 | 用途 |")
    r.append("|------|------|------------|------------|--------|")
    
    vol_data = []
    for city in latest['城市'].unique():
        cd = df[df['城市']==city].sort_values('日期').tail(12)
        if len(cd)<6: continue
        uv = cd['二手住宅价格指数-环比'].std()
        nv = cd['新建商品住宅价格指数-环比'].std()
        tier_val = tier(city)
        vol_data.append({'city':city, 'tier':tier_val, 'uv':uv, 'nv':nv})
    
    vol_df = pd.DataFrame(vol_data).sort_values('uv', ascending=False)
    for _, row in vol_df.head(15).iterrows():
        r.append(f"| {row['city']} | {row['tier']} | {row['uv']:.2f} | {row['nv']:.2f} | 指数波动背景 |")
    
    # === 6. 库存/供给代理 ===
    r.append("\n## 六、新房与二手房同比指数差\n")
    r.append("指数差不能替代库存、供应量、开发商折扣或成交数据。\n")
    r.append("| 城市 | 新房同比 | 二手同比 | 差值 | 用途 |")
    r.append("|------|---------|---------|------|---------|")
    
    for _, row in latest.iterrows():
        gap = row['新建商品住宅价格指数-同比'] - row['二手住宅价格指数-同比']
    gap_data = []
    for _, row in latest.iterrows():
        gap = row['新建商品住宅价格指数-同比'] - row['二手住宅价格指数-同比']
        gap_data.append({'city':row['城市'], 'tier':row['梯队'], 'new_yoy':row['新建商品住宅价格指数-同比'], 'used_yoy':row['二手住宅价格指数-同比'], 'gap':gap})
    
    gap_df = pd.DataFrame(gap_data).sort_values('gap', ascending=False)
    for _, row in gap_df.head(15).iterrows():
        r.append(f"| {row['city']} | {row['new_yoy']:.1f} | {row['used_yoy']:.1f} | {row['gap']:+.1f} | 城市指数背景 |")
    
    # === 7. 领先指标 ===
    r.append("\n## 七、上海指数观察\n")
    r.append("旧领先关系未完成预注册和样本外验证，不可用于预测其他城市。\n")
    
    sh = df[df['城市']=='上海'].sort_values('日期').tail(12)
    r.append("| 月份 | 上海二手环比 | 信号 |")
    r.append("|------|------------|------|")
    for _, row in sh.iterrows():
        mom = row['二手住宅价格指数-环比']
        signal = "✅转正" if mom>=100 else "↓下行" if mom<99.5 else "→企稳"
        r.append(f"| {row['日期'].strftime('%Y-%m')} | {mom:.1f} | {signal} |")
    
    # === 8. 季节性 ===
    r.append("\n## 八、季节性规律\n")
    df['month'] = df['日期'].dt.month
    seasonal = df[(df['日期']<'2026-01') & (df['日期']>='2020-01')].groupby('month')['二手住宅价格指数-环比'].mean()
    r.append("| 月份 | 环比均值 | 特征 |")
    r.append("|------|---------|------|")
    for m, val in seasonal.items():
        feature = "🔥小阳春" if val>100.2 else "→平稳" if val>100 else "↓淡季"
        r.append(f"| {m}月 | {val:.2f} | {feature} |")
    
    # === 9. 建材指数 ===
    r.append("\n## 九、建材指数（房地产投资代理）\n")
    try:
        ci = pd.read_csv(OUTPUT_DIR / "construction_index.csv")
        ci['日期'] = pd.to_datetime(ci['日期'])
        recent_ci = ci.sort_values('日期').tail(5)
        r.append("| 日期 | 建材指数 | 涨跌幅 | 近1年 |")
        r.append("|------|---------|--------|-------|")
        for _, row in recent_ci.iterrows():
            r.append(f"| {row['日期'].strftime('%Y-%m-%d')} | {row['最新值']:.0f} | {row['涨跌幅']:.2f}% | {row['近1年涨跌幅']:.2f}% |")
    except:
        r.append("建材指数数据不可用")
    
    # === 10. REITs ===
    r.append("\n## 十、房地产REITs市场\n")
    try:
        reits = pd.read_csv(OUTPUT_DIR / "reits.csv")
        r.append(f"当前上市REITs: {len(reits)}只")
        r.append(f"| 名称 | 最新价 | 涨跌幅 | 成交额 |")
        r.append(f"|------|--------|--------|--------|")
        for _, row in reits.head(10).iterrows():
            r.append(f"| {row['名称']} | {row['最新价']:.3f} | {row['涨跌幅']:.2f}% | {row['成交额']/10000:.0f}万 |")
    except:
        r.append("REITs数据不可用")
    
    return "\n".join(r)


if __name__ == "__main__":
    raise SystemExit(
        "DISABLED_LEGACY_MEGA_REPORT: heuristic regime, timing, and ranking "
        "labels are not validated property-level evidence"
    )
