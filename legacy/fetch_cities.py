#!/usr/bin/env python3
"""Fetch the monitored-city price index dataset without partial overwrite."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


OUTPUT_DIR = Path(__file__).resolve().parent
TARGET = OUTPUT_DIR / "70city_full.csv"

# This legacy pipeline currently monitors 42 cities; the filename is retained
# for compatibility with existing reports.
CITIES = [
    "北京", "上海", "广州", "深圳", "天津", "重庆", "杭州", "南京",
    "武汉", "成都", "西安", "长沙", "郑州", "洛阳", "青岛", "大连",
    "宁波", "厦门", "合肥", "昆明", "贵阳", "南昌", "福州", "济南",
    "沈阳", "哈尔滨", "长春", "南宁", "太原", "石家庄", "乌鲁木齐",
    "无锡", "温州", "烟台", "泉州", "惠州", "徐州", "金华", "唐山",
    "三亚", "桂林", "扬州",
]

PRICE_INDEX_COLUMNS = (
    "新建商品住宅价格指数-同比",
    "新建商品住宅价格指数-环比",
    "二手住宅价格指数-同比",
    "二手住宅价格指数-环比",
)
REQUIRED_COLUMNS = {"日期", "城市", *PRICE_INDEX_COLUMNS}


def validate_latest_cross_section(
    frame: pd.DataFrame,
    expected_cities: Iterable[str],
    *,
    context: str = "数据集",
) -> pd.DataFrame:
    """Validate one complete, contemporaneous latest city cross-section."""
    expected = tuple(expected_cities)
    if not expected or len(set(expected)) != len(expected):
        raise ValueError(f"{context}的配置城市为空或重复")

    missing_columns = REQUIRED_COLUMNS.difference(frame.columns)
    if missing_columns:
        raise ValueError(
            f"{context}缺少字段: {', '.join(sorted(missing_columns))}"
        )
    if frame.empty:
        raise ValueError(f"{context}为空")

    validated = frame.copy()
    validated["日期"] = pd.to_datetime(validated["日期"], errors="raise")
    if validated["日期"].isna().any():
        raise ValueError(f"{context}存在空日期")
    if validated["城市"].isna().any():
        raise ValueError(f"{context}存在空城市")

    present = set(validated["城市"].unique())
    expected_set = set(expected)
    missing_cities = sorted(expected_set - present)
    unexpected_cities = sorted(present - expected_set)
    if missing_cities or unexpected_cities:
        details = []
        if missing_cities:
            details.append("缺少 " + "、".join(missing_cities))
        if unexpected_cities:
            details.append("未配置 " + "、".join(unexpected_cities))
        raise ValueError(f"{context}城市覆盖不完整: {'; '.join(details)}")

    duplicates = validated.duplicated(["城市", "日期"], keep=False)
    if duplicates.any():
        duplicate_keys = (
            validated.loc[duplicates, ["城市", "日期"]]
            .drop_duplicates()
            .sort_values(["城市", "日期"])
        )
        sample = "、".join(
            f"{row['城市']}@{row['日期']:%Y-%m-%d}"
            for _, row in duplicate_keys.head(5).iterrows()
        )
        raise ValueError(f"{context}存在重复的城市-日期记录: {sample}")

    latest_date = validated["日期"].max()
    city_latest = validated.groupby("城市", sort=True)["日期"].max()
    lagging = city_latest[city_latest != latest_date]
    if not lagging.empty:
        detail = "、".join(
            f"{city}={date:%Y-%m-%d}" for city, date in lagging.items()
        )
        raise ValueError(
            f"{context}最新观察期不一致; 全局={latest_date:%Y-%m-%d}; "
            f"落后城市: {detail}"
        )

    # Numeric conversion makes empty strings and malformed provider values fail
    # the same gate as explicit nulls.
    for column in PRICE_INDEX_COLUMNS:
        validated[column] = pd.to_numeric(validated[column], errors="coerce")
    latest = validated[validated["日期"] == latest_date]
    invalid_latest = latest[list(PRICE_INDEX_COLUMNS)].isna() | ~np.isfinite(
        latest[list(PRICE_INDEX_COLUMNS)]
    )
    if invalid_latest.any().any():
        bad = []
        for row_index, column in zip(*np.where(invalid_latest.to_numpy())):
            bad.append(f"{latest.iloc[row_index]['城市']}:{column}")
        raise ValueError(
            f"{context}最新期关键字段为空或非有限值: "
            + "、".join(bad[:10])
        )

    return validated.sort_values(["城市", "日期"]).reset_index(drop=True)


def validate_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate the configured main-city publication boundary."""
    return validate_latest_cross_section(
        frame, CITIES, context="主城市抓取数据"
    )


def fetch_all() -> pd.DataFrame:
    """Fetch every configured city; one failure rejects the whole refresh."""
    try:
        import akshare as ak
    except ImportError as exc:
        raise RuntimeError("缺少依赖 akshare；现有已验证数据未被修改") from exc

    all_data = []
    failures = []
    for index, city in enumerate(CITIES, 1):
        print(f"[{index}/{len(CITIES)}] 拉取 {city}...", end="", flush=True)
        try:
            frame = ak.macro_china_new_house_price(
                city_first=city, city_second=city
            )
            if frame.empty:
                raise ValueError("空数据")
            frame = frame.copy()
            frame["城市"] = city
            all_data.append(frame)
            print(f" 完成 ({len(frame)} 行)")
        except Exception as exc:  # Network/provider errors are reported together.
            failures.append(f"{city}: {exc}")
            print(f" 失败 ({exc})")

    if failures:
        raise RuntimeError(
            "抓取不完整，拒绝覆盖现有数据: " + "; ".join(failures)
        )
    return validate_dataset(pd.concat(all_data, ignore_index=True))


def atomic_write_csv(frame: pd.DataFrame, target: Path = TARGET) -> None:
    """Publish a complete dataset with an atomic same-directory rename."""
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=target.parent,
        prefix=f".{target.name}.",
        suffix=".tmp",
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        frame.to_csv(temporary, index=False)
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    try:
        combined = fetch_all()
        atomic_write_csv(combined)
    except Exception as exc:
        print(f"\n更新失败: {exc}")
        return 1

    print(
        f"\n更新完成: {len(combined)} 行, {combined['城市'].nunique()} 城; "
        f"数据期 {combined['日期'].min():%Y-%m} ~ {combined['日期'].max():%Y-%m}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
