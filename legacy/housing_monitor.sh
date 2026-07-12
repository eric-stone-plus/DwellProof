#!/bin/bash
# 城市价格指数背景刷新脚本 — 每月运行
# 用法: bash housing_monitor.sh

set -e

OUTPUT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
DATE=$(date +%Y%m%d)
PYTHON="${PYTHON:-python3}"

echo "=== 房价监测自动化 $DATE ==="

echo "1. 拉取最新城市数据..."
"$PYTHON" "$OUTPUT_DIR/fetch_cities.py"

echo "2. 合并扩展城市数据..."
"$PYTHON" "$OUTPUT_DIR/fetch_more_cities.py"

echo "3. 生成不可操作的市场背景报告..."
"$PYTHON" "$OUTPUT_DIR/legacy_main.py"

# Do not copy archived predictions or recommendations into a fresh backup.
echo "4. 备份已刷新数据和市场背景报告..."
mkdir -p "$OUTPUT_DIR/backup/$DATE"
cp "$OUTPUT_DIR/70city_full.csv" "$OUTPUT_DIR/backup/$DATE/"
cp "$OUTPUT_DIR/70city_expanded.csv" "$OUTPUT_DIR/backup/$DATE/"
cp "$OUTPUT_DIR/LEGACY_MARKET_CONTEXT.md" "$OUTPUT_DIR/backup/$DATE/"
cp "$OUTPUT_DIR"/city_*.csv "$OUTPUT_DIR/backup/$DATE/" 2>/dev/null || true

echo "=== 完成 ==="
echo "市场背景报告: $OUTPUT_DIR/LEGACY_MARKET_CONTEXT.md"
echo "备份: $OUTPUT_DIR/backup/$DATE/"
