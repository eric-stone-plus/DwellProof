#!/usr/bin/env python3
"""Fetch extra cities and rebuild the expanded dataset fail-closed."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from fetch_cities import (
    PRICE_INDEX_COLUMNS,
    validate_dataset as validate_main_dataset,
    validate_latest_cross_section,
)


OUTPUT = Path(__file__).resolve().parent
EXTRA_CITIES = [
    "佛山", "东莞", "中山", "江门", "珠海",
    "苏州", "常州", "嘉兴", "绍兴", "芜湖",
]
REQUIRED_COLUMNS = {"日期", "城市", *PRICE_INDEX_COLUMNS}


def _validate_city(frame: pd.DataFrame, city: str) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"{city} 缺少字段: {', '.join(sorted(missing))}")
    frame = frame.copy()
    frame["日期"] = pd.to_datetime(frame["日期"], errors="raise")
    if frame["日期"].isna().any():
        raise ValueError(f"{city} 存在空日期")
    if frame.empty or set(frame["城市"].unique()) != {city}:
        raise ValueError(f"{city} 数据为空或城市字段不一致")
    if frame.duplicated(["城市", "日期"]).any():
        raise ValueError(f"{city} 存在重复日期")
    for column in PRICE_INDEX_COLUMNS:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    latest = frame.loc[frame["日期"] == frame["日期"].max()]
    invalid = latest[list(PRICE_INDEX_COLUMNS)].isna() | ~np.isfinite(
        latest[list(PRICE_INDEX_COLUMNS)]
    )
    if invalid.any().any():
        raise ValueError(f"{city} 最新期关键价格指数为空或非有限值")
    return frame.sort_values("日期")


def validate_fetched_batch(
    fetched: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """Require every configured extra city in one complete latest period."""
    present = set(fetched)
    expected = set(EXTRA_CITIES)
    if present != expected:
        missing = "、".join(sorted(expected - present)) or "无"
        unexpected = "、".join(sorted(present - expected)) or "无"
        raise ValueError(
            f"扩展抓取批次城市覆盖不完整: 缺少 {missing}; 未配置 {unexpected}"
        )

    normalized = [_validate_city(fetched[city], city) for city in EXTRA_CITIES]
    validated = validate_latest_cross_section(
        pd.concat(normalized, ignore_index=True),
        EXTRA_CITIES,
        context="扩展城市当次抓取批次",
    )
    return {
        city: validated.loc[validated["城市"] == city].reset_index(drop=True)
        for city in EXTRA_CITIES
    }


def validate_publication_boundary(
    main: pd.DataFrame,
    fetched: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    """Validate fresh main/extra inputs; retained city files may be historical."""
    validated_main = validate_main_dataset(main)
    validated_fetched = validate_fetched_batch(fetched)
    main_latest = validated_main["日期"].max()
    extra_latest = max(frame["日期"].max() for frame in validated_fetched.values())
    if main_latest != extra_latest:
        raise ValueError(
            "主数据与当次扩展抓取观察期不一致: "
            f"主数据={main_latest:%Y-%m-%d}; 扩展={extra_latest:%Y-%m-%d}"
        )
    return validated_main, validated_fetched


def fetch_extras() -> dict[str, pd.DataFrame]:
    try:
        import akshare as ak
    except ImportError as exc:
        raise RuntimeError("缺少依赖 akshare；扩展数据未被修改") from exc

    fetched = {}
    failures = []
    for city in EXTRA_CITIES:
        print(f"拉取 {city}...", end="", flush=True)
        try:
            frame = ak.macro_china_new_house_price(
                city_first=city, city_second=city
            )
            if frame.empty:
                raise ValueError("空数据")
            frame = frame.copy()
            frame["城市"] = city
            fetched[city] = _validate_city(frame, city)
            print(f" 完成 ({len(frame)} 行)")
        except Exception as exc:  # Provider errors must not produce partial data.
            failures.append(f"{city}: {exc}")
            print(f" 失败 ({exc})")
    if failures:
        raise RuntimeError(
            "扩展城市抓取不完整，拒绝覆盖: " + "; ".join(failures)
        )
    return validate_fetched_batch(fetched)


def build_expanded(
    main: pd.DataFrame, extra_frames: list[pd.DataFrame]
) -> pd.DataFrame:
    """Combine validated sources; main wins only for cross-source overlaps."""
    sources = []
    for position, source in enumerate([main, *extra_frames]):
        label = "主数据" if position == 0 else f"扩展来源{position}"
        missing = REQUIRED_COLUMNS.difference(source.columns)
        if missing:
            raise ValueError(
                f"{label}缺少字段: {', '.join(sorted(missing))}"
            )
        normalized = source.copy()
        normalized["日期"] = pd.to_datetime(normalized["日期"], errors="raise")
        if normalized.duplicated(["城市", "日期"]).any():
            raise ValueError(f"{label}内部存在重复的城市-日期记录")
        for column in PRICE_INDEX_COLUMNS:
            normalized[column] = pd.to_numeric(
                normalized[column], errors="coerce"
            )
        sources.append(normalized)

    combined = pd.concat(sources, ignore_index=True)
    # The main monitored dataset is canonical for overlapping cities.
    combined = combined.drop_duplicates(["城市", "日期"], keep="first")
    if combined.duplicated(["城市", "日期"]).any():
        raise ValueError("扩展合并结果存在重复的城市-日期记录")
    return combined.sort_values(["城市", "日期"]).reset_index(drop=True)


def atomic_write_csv(frame: pd.DataFrame, target: Path) -> None:
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
        fetched = fetch_extras()
        main_frame = pd.read_csv(OUTPUT / "70city_full.csv")
        main_frame, fetched = validate_publication_boundary(
            main_frame, fetched
        )

        retained = []
        fetched_names = set(fetched)
        for path in sorted(OUTPUT.glob("city_*.csv")):
            city = path.stem.removeprefix("city_")
            if city not in fetched_names:
                retained.append(_validate_city(pd.read_csv(path), city))

        expanded = build_expanded(
            main_frame, retained + list(fetched.values())
        )
        for city, frame in fetched.items():
            atomic_write_csv(frame, OUTPUT / f"city_{city}.csv")
        atomic_write_csv(expanded, OUTPUT / "70city_expanded.csv")
    except Exception as exc:
        print(f"\n更新失败: {exc}")
        return 1

    print(
        f"\n扩展数据更新完成: {expanded['城市'].nunique()} 城, "
        f"{len(expanded)} 行"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
