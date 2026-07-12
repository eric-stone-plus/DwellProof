#!/usr/bin/env python3
"""
内地房价监测系统 — 自动化监测脚本
每日/每周运行，拉取最新数据并生成监测报告
"""

import pandas as pd
from datetime import datetime
from pathlib import Path

from fetch_cities import (
    atomic_write_csv,
    validate_latest_cross_section,
)

OUTPUT_DIR = Path(__file__).resolve().parent

# 监测城市列表
MONITOR_CITIES = {
    'T1': ['北京', '上海', '广州', '深圳'],
    'T2': ['杭州', '成都', '武汉', '南京', '重庆', '天津', '西安', '长沙', '郑州'],
    'T3': ['合肥', '沈阳', '乌鲁木齐', '大连', '宁波', '厦门', '福州', '济南', '青岛',
           '昆明', '贵阳', '南昌', '南宁', '太原', '石家庄', '长春', '哈尔滨',
           '无锡', '温州', '烟台', '惠州', '徐州', '金华', '唐山', '三亚']
}

def configured_cities():
    """Return the configured city sequence and reject duplicate ownership."""
    cities = [city for tier in MONITOR_CITIES.values() for city in tier]
    if len(cities) != len(set(cities)):
        raise ValueError("监测城市配置存在重复城市")
    return cities


def validate_monitoring_dataset(df):
    """Gate reports and published CSVs on a complete latest cross-section."""
    validated = validate_latest_cross_section(
        df,
        configured_cities(),
        context="监测数据",
    )
    if "梯队" not in validated.columns:
        raise ValueError("监测数据缺少字段: 梯队")

    expected_tiers = {
        city: tier
        for tier, cities in MONITOR_CITIES.items()
        for city in cities
    }
    actual_tiers = validated.groupby("城市")["梯队"].agg(
        lambda values: set(values.dropna())
    )
    inconsistent = []
    for city, expected in expected_tiers.items():
        if actual_tiers.get(city, set()) != {expected}:
            inconsistent.append(
                f"{city}=实际{sorted(actual_tiers.get(city, set()))}/配置{expected}"
            )
    if inconsistent:
        raise ValueError("监测数据梯队不一致: " + "、".join(inconsistent))
    return validated


def publish_latest_data(df, target=None):
    """Revalidate and atomically publish a monitoring dataset."""
    target = Path(target) if target is not None else OUTPUT_DIR / "latest_data.csv"
    validated = validate_monitoring_dataset(df)
    atomic_write_csv(validated, target)


def fetch_latest_data():
    """拉取最新数据"""
    try:
        import akshare as ak
    except ImportError as exc:
        raise RuntimeError("缺少依赖 akshare，未生成或覆盖监测数据") from exc
    all_data = []
    all_cities = []
    for tier, cities in MONITOR_CITIES.items():
        all_cities.extend([(c, tier) for c in cities])
    
    failures = []
    for city, tier in all_cities:
        try:
            df = ak.macro_china_new_house_price(city_first=city, city_second=city)
            if len(df) > 0:
                df['城市'] = city
                df['梯队'] = tier
                all_data.append(df)
        except Exception as exc:
            failures.append(f"{city}: {exc}")

    if failures:
        raise RuntimeError("监测抓取不完整，拒绝发布: " + "; ".join(failures))
    
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        return validate_monitoring_dataset(combined)
    raise RuntimeError("监测抓取没有返回任何数据，拒绝发布")


def generate_monitoring_report(df):
    """Render descriptive city-index context without heuristic labels."""
    df = validate_monitoring_dataset(df)
    latest_date = df['日期'].max()
    latest = df[df['日期'] == latest_date]
    
    r = [
        "> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | "
        "`actionable: false`  ",
        "> 本文件来自已退役的原 HouseAlice 原型，不属于 DwellProof。内容未经标的、产权、"
        "税费、贷款及成交证据核验，不得用于买卖、估值、预测、排名或风险判断。"
        "DwellProof 入口：`../web/`。\n",
    ]
    r.append(f"# 内地房价监测报告 — {latest_date.strftime('%Y-%m')}")
    r.append(f"\n> 自动生成 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    r.append("> 数据源声明: akshare 接口返回的国家统计局城市指数；"
             "需以官方原表复核后才能提升证据等级")
    r.append("> 仅作市场背景；不生成预警、周期标签、跨城预测或交易建议。")
    
    # 梯队汇总
    r.append("\n## 梯队汇总\n")
    r.append("| 梯队 | 城市数 | 新房环比均值 | 二手环比均值 | 新房同比均值 | 二手同比均值 |")
    r.append("|------|--------|------------|------------|------------|------------|")
    
    for tier in ['T1', 'T2', 'T3']:
        tier_data = latest[latest['梯队'] == tier]
        if len(tier_data) == 0:
            continue
        tier_name = {'T1': '一线', 'T2': '强二线', 'T3': '二三线'}[tier]
        new_mom = tier_data['新建商品住宅价格指数-环比'].mean()
        used_mom = tier_data['二手住宅价格指数-环比'].mean()
        new_yoy = tier_data['新建商品住宅价格指数-同比'].mean()
        used_yoy = tier_data['二手住宅价格指数-同比'].mean()
        
        r.append(f"| {tier_name} | {len(tier_data)} | {new_mom:.2f} | {used_mom:.2f} | {new_yoy:.1f} | {used_yoy:.1f} |")
    
    r.append("\n## 上海同期指数观察\n")
    sh_data = df[df['城市'] == '上海'].sort_values('日期').tail(6)
    r.append("| 月份 | 新房环比 | 二手环比 | 新房同比 | 二手同比 |")
    r.append("|------|---------|---------|---------|---------|")
    for _, row in sh_data.iterrows():
        r.append(f"| {row['日期'].strftime('%Y-%m')} | {row['新建商品住宅价格指数-环比']:.1f} | {row['二手住宅价格指数-环比']:.1f} | {row['新建商品住宅价格指数-同比']:.1f} | {row['二手住宅价格指数-同比']:.1f} |")
    
    r.append("\n城市指数不能替代具体房源成交、产权、税费、贷款或现金流证据。")
    
    return "\n".join(r)


if __name__ == "__main__":
    print("=" * 60)
    print("  内地房价监测系统 — 自动监测")
    print("=" * 60)
    
    print("\n拉取最新数据...")
    try:
        df = fetch_latest_data()
    except Exception as exc:
        print(f"数据拉取失败: {exc}")
        raise SystemExit(1)
    
    if df is not None:
        print(f"获取 {df['城市'].nunique()} 城, {len(df)} 条记录")
        
        report = generate_monitoring_report(df)
        
        out_path = OUTPUT_DIR / f"monitoring_report_{datetime.now().strftime('%Y%m%d')}.md"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n报告已保存: {out_path}")
        print(f"报告长度: {len(report)} 字符")
        
        # 发布前重新执行同期截面门禁，并使用同目录原子替换。
        publish_latest_data(df)
    else:
        print("数据拉取失败")
        raise SystemExit(1)
