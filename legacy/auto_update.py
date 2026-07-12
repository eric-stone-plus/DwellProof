#!/usr/bin/env python3
"""Refresh legacy city-index data and publish a market-context-only report."""

import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent

# Directional analysis, prediction, and ranking generators are intentionally
# excluded from the default path. They remain archived for traceability only.
SAFE_UPDATE_STEPS = (
    ("fetch_cities.py", "1. 拉取最新城市指数数据"),
    ("fetch_more_cities.py", "2. 合并扩展城市指数数据"),
    ("legacy_main.py", "3. 生成不可操作的市场背景报告"),
)

SAFE_BACKUP_NAMES = (
    "70city_full.csv",
    "70city_expanded.csv",
    "LEGACY_MARKET_CONTEXT.md",
)


def run_script(script_name, desc):
    """运行脚本"""
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"{'='*60}")
    
    script_path = OUTPUT / script_name
    if not script_path.exists():
        print(f"  ⚠️ 脚本不存在: {script_name}")
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=300,
        )
        print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
        if result.returncode != 0:
            print(f"  ❌ 失败: {result.stderr[-200:]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print(f"  ⏰ 超时")
        return False
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False


def main() -> int:
    """主函数"""
    print("=" * 60)
    print(f"  旧原型安全更新 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    
    for script, description in SAFE_UPDATE_STEPS:
        if not run_script(script, description):
            print(f"\n❌ 更新中止: {description} 失败；未声明成功，也未创建成功备份")
            return 1

    # Back up only refreshed data and the safe compatibility report. Historical
    # prediction and recommendation artifacts must not receive a fresh datestamp.
    backup_dir = OUTPUT / "backup" / datetime.now().strftime('%Y%m%d')
    backup_dir.mkdir(parents=True, exist_ok=True)

    backup_sources = [OUTPUT / name for name in SAFE_BACKUP_NAMES]
    backup_sources.extend(sorted(OUTPUT.glob("city_*.csv")))
    for src in backup_sources:
        if src.is_file():
            shutil.copy2(src, backup_dir / src.name)
    
    print(f"\n{'='*60}")
    print(f"  ✅ 更新完成")
    print(f"  市场背景报告: {OUTPUT / 'LEGACY_MARKET_CONTEXT.md'}")
    print(f"  备份: {backup_dir}/")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
