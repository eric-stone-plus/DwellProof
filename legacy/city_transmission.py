#!/usr/bin/env python3
"""Archived city-transmission model; execution and import are disabled."""

raise SystemExit(
    "DISABLED_LEGACY_CITY_TRANSMISSION: exploratory lead-lag correlations and "
    "regime labels are not validated predictive evidence"
)

import pandas as pd
import numpy as np
from pathlib import Path

from analysis_utils import best_lag_correlation

OUTPUT = Path(__file__).resolve().parent

# 加载数据
hp = pd.read_csv(OUTPUT / "70city_expanded.csv")
hp['日期'] = pd.to_datetime(hp['日期'])
hp = hp.drop_duplicates(subset=['城市', '日期'])

r = []
r.append("# 📈 城市间传导模型 + 数据可视化增强\n")
r.append(f"> MAGI v1.0 | {hp['城市'].nunique()}城 × {len(hp)}条")

# 1. 城市间相关性矩阵
r.append("\n## 一、城市间二手房环比相关性矩阵\n")
cities = ['上海','北京','广州','深圳','杭州','成都','武汉','南京','天津','重庆','西安','郑州','长沙','长春']
available = [c for c in cities if c in hp['城市'].values]
pivot = hp.pivot_table(index='日期', columns='城市', values='二手住宅价格指数-环比')
sub = pivot[available].dropna()
corr = sub.corr()

r.append("```")
header = f"{'':>6}" + "".join(f"{c:>6}" for c in available)
r.append(header)
for c1 in available:
    row = f"{c1:>6}"
    for c2 in available:
        row += f"{corr.loc[c1,c2]:>6.2f}"
    r.append(row)
r.append("```")

# 2. 集群分析
r.append("\n## 二、城市集群分析\n")
r.append("相关性>0.7的城市归为同一集群:\n")

clusters = {}
assigned = set()
for c1 in available:
    if c1 in assigned: continue
    cluster = [c1]
    assigned.add(c1)
    for c2 in available:
        if c2 in assigned: continue
        if corr.loc[c1, c2] > 0.7:
            cluster.append(c2)
            assigned.add(c2)
    if len(cluster) > 1:
        clusters[c1] = cluster

for name, members in clusters.items():
    r.append(f"- **{name}集群**: {', '.join(members)}")

# 3. 领先滞后关系
r.append("\n## 三、领先滞后关系（上海为基准）\n")
r.append("| 领先城市 | 滞后城市 | 领先月数 | 相关系数 | 含义 |")
r.append("|---------|---------|---------|---------|------|")

sh = pivot['上海'].dropna()
for city in available:
    if city == '上海': continue
    other = pivot[city].dropna()
    common = sh.index.intersection(other.index)
    if len(common) < 24: continue
    
    best_lag, best_corr = best_lag_correlation(
        sh[common].values, other[common].values
    )
    
    if best_lag > 0:
        meaning = f"探索性相关在+{best_lag}月最大（不可预测）"
    elif best_lag < 0:
        meaning = f"探索性相关在{best_lag}月最大（不可预测）"
    else:
        meaning = "同步"
    
    r.append(f"| 上海 | {city} | {best_lag:+d}月 | {best_corr:.3f} | {meaning} |")

# 4. 各城市近12月走势
r.append("\n## 四、各城市近12月二手房环比走势\n")
r.append("```")
for city in ['上海','北京','广州','深圳','杭州','成都','武汉','南京','天津','重庆']:
    cd = hp[hp['城市']==city].sort_values('日期').tail(12)
    if len(cd) < 12: continue
    vals = cd['二手住宅价格指数-环比'].values
    bars = ""
    for v in vals:
        if v >= 100.3: bars += "█"
        elif v >= 100.0: bars += "▓"
        elif v >= 99.7: bars += "▒"
        elif v >= 99.4: bars += "░"
        else: bars += "·"
    r.append(f"  {city:>4}: {bars} ({vals[-1]:.1f})")
r.append("```")

# 5. 各城市同比走势
r.append("\n## 五、各城市近12月二手房同比走势\n")
r.append("```")
for city in ['上海','北京','广州','深圳','杭州','成都','武汉','南京','天津','重庆']:
    cd = hp[hp['城市']==city].sort_values('日期').tail(12)
    if len(cd) < 12: continue
    vals = cd['二手住宅价格指数-同比'].values
    bars = ""
    for v in vals:
        if v >= 98: bars += "█"
        elif v >= 95: bars += "▓"
        elif v >= 93: bars += "▒"
        elif v >= 91: bars += "░"
        else: bars += "·"
    r.append(f"  {city:>4}: {bars} ({vals[-1]:.1f})")
r.append("```")

# 6. 区域汇总
r.append("\n## 六、区域汇总\n")
region_map = {
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

latest = hp[hp['日期'] == hp['日期'].max()].copy()
latest['区域'] = latest['城市'].map(region_map).fillna('其他')

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

report = "\n".join(r)
with open(OUTPUT / "CITY_TRANSMISSION_MODEL.md", "w", encoding="utf-8") as f:
    f.write(report)
print(f"报告: {len(report)}字符, {len(report.splitlines())}行")
