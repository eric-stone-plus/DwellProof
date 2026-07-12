> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | `actionable: false`  
> 本文件来自已退役的原 HouseAlice 原型，仅保留旧研究过程，不属于 DwellProof 产品。内容未经标的、产权、税费、贷款及成交证据核验，可能错误或过期，不得用于买卖、估值、预测、排名或风险判断。DwellProof 入口：`../web/`。

# 🚀 HouseAlice 部署指南

> 2026-06-14

---

## 一、环境要求

| 依赖 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 核心运行环境 |
| pandas | 1.5+ | 数据处理 |
| numpy | 1.20+ | 数值计算 |
| akshare | 1.10+ | 数据源 |

---

## 二、安装步骤

### 2.1 克隆项目

```bash
cd ~/Downloads/DEVELOPMENT
# 项目已存在，无需克隆
```

### 2.2 创建虚拟环境

```bash
cd ~/Downloads/DEVELOPMENT/quinte-housing
python3 -m venv .venv
source .venv/bin/activate
pip install pandas numpy akshare
```

### 2.3 验证安装

```bash
python3 housealice_test.py
# 预期: 7/7 测试通过
```

---

## 三、使用方式

### 3.1 命令行

```bash
# 查看仪表板
python3 housealice_main.py

# 查看预警
python3 housealice_alert.py

# 查看决策信号
python3 housealice_decision.py

# 查看风险评分
python3 housealice_risk.py

# 运行测试
python3 housealice_test.py

# 自动更新
python3 auto_update.py
```

### 3.2 Python代码

```python
from housealice_mcp import HouseAliceMCP

mcp = HouseAliceMCP()

# 获取城市数据
data = mcp.call_tool('housing_get_city_data', city='广州')

# 获取买房信号
signal = mcp.call_tool('housing_get_buy_signal', city='广州')

# 获取投资排名
ranking = mcp.call_tool('housing_get_investment_ranking')
```

### 3.3 Web UI

```bash
# 打开仪表板
open HOUSEALICE_WEB.html
```

---

## 四、自动化

### 4.1 Cron Job

已设置每月20日自动运行：
```
0 9 20 * * python3 auto_update.py
```

### 4.2 手动更新

```bash
python3 auto_update.py
```

---

## 五、故障排除

| 问题 | 解决方案 |
|------|---------|
| 数据拉取失败 | 检查网络/代理 |
| 报告为空 | 检查数据文件是否存在 |
| 预警不触发 | 检查阈值设置 |
| 决策信号异常 | 检查数据质量 |
| 测试失败 | 检查依赖安装 |

---

## 六、目录结构

```
~/Downloads/DEVELOPMENT/quinte-housing/
├── housealice_*.py (8个组件)
├── auto_update.py
├── housealice_test.py
├── *.md (98个报告)
├── *.html (4个仪表板)
├── *.csv (47个数据文件)
└── .venv (虚拟环境)
```

---

*部署指南 | 2026-06-14*
