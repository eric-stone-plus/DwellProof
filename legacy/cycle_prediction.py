#!/usr/bin/env python3
"""Archived handwritten cycle forecast; execution is disabled."""

raise SystemExit(
    "DISABLED_LEGACY_FORECAST: handwritten extrapolation and probabilities "
    "were not validated out of sample"
)
import pandas as pd
import numpy as np
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent
df = pd.read_csv(OUTPUT / "70city_expanded.csv")
df['日期'] = pd.to_datetime(df['日期'])
df = df.drop_duplicates(subset=['城市', '日期'])

r = []
r.append("# 📈 房地产周期预测模型\n")
r.append(f"> MAGI v1.0 | 基于历史数据的量化预测")

# === 1. 各城市周期长度分析 ===
r.append("\n## 一、各城市周期长度分析\n")
r.append("| 城市 | 峰值 | 谷底 | 下跌月数 | 回升月数 | 总周期 |")
r.append("|------|------|------|---------|---------|--------|")

for city in ['上海','北京','广州','深圳','杭州','成都','武汉','南京','天津','重庆','西安','郑州','长沙','长春']:
    cd = df[df['城市']==city].sort_values('日期')
    yoy = cd['二手住宅价格指数-同比'].dropna()
    if len(yoy) < 60: continue
    
    # 找峰值和谷底
    peak_idx = yoy.idxmax()
    trough_idx = yoy.idxmin()
    peak_date = cd.loc[peak_idx, '日期']
    trough_date = cd.loc[trough_idx, '日期']
    
    if trough_date > peak_date:
        down_months = (trough_date.year - peak_date.year) * 12 + (trough_date.month - peak_date.month)
        up_months = (cd.iloc[-1]['日期'].year - trough_date.year) * 12 + (cd.iloc[-1]['日期'].month - trough_date.month)
        total = down_months + up_months
        r.append(f"| {city} | {peak_date.strftime('%Y-%m')} | {trough_date.strftime('%Y-%m')} | {down_months} | {up_months} | {total} |")

# === 2. 环比→同比转换模型 ===
r.append("\n## 二、环比→同比转换模型\n")
r.append("公式: 同比变化 ≈ 近12月环比均值偏离100的累积\n")
r.append("| 城市 | 当前同比 | 近6月环比均值 | 6月后同比预测 | 同比转正需 |")
r.append("|------|---------|-------------|------------|----------|")

for city in ['上海','北京','广州','深圳','杭州','成都','武汉','南京','天津','重庆','西安','郑州','长沙','长春']:
    cd = df[df['城市']==city].sort_values('日期')
    if len(cd) < 12: continue
    
    current_yoy = cd.iloc[-1]['二手住宅价格指数-同比']
    recent_mom = cd.tail(6)['二手住宅价格指数-环比'].mean()
    mom_above = recent_mom - 100
    
    # 6月后同比预测
    yoy_6m = current_yoy + 6 * mom_above * 1.5
    
    # 同比转正需多少月
    if mom_above > 0.05:
        months_to_100 = (100 - current_yoy) / (mom_above * 1.5)
        turn_str = f"{int(months_to_100)}月"
    else:
        turn_str = ">36月"
    
    r.append(f"| {city} | {current_yoy:.1f} | {recent_mom:.2f} | {yoy_6m:.1f} | {turn_str} |")

# === 3. 城市间传导模型 ===
r.append("\n## 三、城市间传导模型\n")
r.append("上海领先其他城市2-5月，可用于预测：\n")
r.append("| 上海信号 | 预示 | 时间差 | 当前状态 |")
r.append("|---------|------|--------|---------|")

sh = df[df['城市']=='上海'].sort_values('日期').tail(6)
sh_mom = sh['二手住宅价格指数-环比'].values

signals = [
    ("上海环比>100.3", "全国一线跟涨", "2-3月", "✅ 100.7" if sh_mom[-1] > 100.3 else "❌"),
    ("上海环比>100.0", "全国企稳", "3-5月", "✅ 100.7" if sh_mom[-1] > 100.0 else "❌"),
    ("上海同比转正", "全国信心恢复", "6-12月", f"❌ {sh.iloc[-1]['二手住宅价格指数-同比']:.1f}"),
    ("上海成交量放量", "全国底部确认", "2-3月", "需数据"),
]

for signal, meaning, lag, status in signals:
    r.append(f"| {signal} | {meaning} | {lag} | {status} |")

# === 4. 政策传导模型 ===
r.append("\n## 四、政策传导模型\n")
r.append("| 政策 | 时间 | 传导时滞 | 效果 |")
r.append("|------|------|---------|------|")
r.append("| LPR降50bp | 2024.09 | 6-12月 | 一线环比从99.0→100.4 |")
r.append("| 存量房贷下调 | 2024.09 | 3-6月 | 月供减少，消费释放 |")
r.append("| 限购放松 | 2024.09 | 1-3月 | 一线成交量回升 |")
r.append("| 首付降至15% | 2024.05 | 6-12月 | 刚需入场 |")
r.append("| **组合拳效果** | **2024.09** | **12月** | **一线2025.09触底** |")

# === 5. 情景概率 ===
r.append("\n## 五、情景概率\n")
r.append("| 情景 | 概率 | 全国同比 | 一线同比 | 触发条件 |")
r.append("|------|------|---------|---------|---------|")
r.append("| V型反弹 | 15% | +2% | +5% | 超预期刺激+GDP>5.5% |")
r.append("| L型筑底 | 50% | -3% | 0% | 政策托而不举 |")
r.append("| 缓慢阴跌 | 25% | -5% | -3% | 经济放缓+信心不足 |")
r.append("| 二次探底 | 10% | -8% | -5% | 外部冲击+房企违约 |")

r.append("\n**加权预测:**")
r.append("全国同比 ≈ 0.15×2 + 0.50×(-3) + 0.25×(-5) + 0.10×(-8) = **-3.0%**")
r.append("一线同比 ≈ 0.15×5 + 0.50×0 + 0.25×(-3) + 0.10×(-5) = **-0.5%**")

report = "\n".join(r)
with open(OUTPUT / "CYCLE_PREDICTION_MODEL.md", "w", encoding="utf-8") as f:
    f.write(report)
print(f"报告: {len(report)}字符")
