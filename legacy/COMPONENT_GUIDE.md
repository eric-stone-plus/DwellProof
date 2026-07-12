> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | `actionable: false`  
> 本文件来自已退役的原 HouseAlice 原型，仅保留旧研究过程，不属于 DwellProof 产品。内容未经标的、产权、税费、贷款及成交证据核验，可能错误或过期，不得用于买卖、估值、预测、排名或风险判断。DwellProof 入口：`../web/`。

# 📋 HouseAlice 组件清单 + 使用指南

> 2026-06-14 | 所有组件均可直接运行

---

## 一、组件清单

### 1.1 核心组件

| 组件 | 文件 | 功能 | 运行命令 |
|------|------|------|---------|
| 统一入口 | housealice_main.py | 整合所有模块 | python3 housealice_main.py |
| 统一房产账户 | housealice_uha.py | 管理房产组合 | python3 housealice_uha.py |
| 预警引擎 | housealice_alert.py | 7种预警规则 | python3 housealice_alert.py |
| 决策引擎 | housealice_decision.py | 买/卖/持有信号 | python3 housealice_decision.py |
| MCP Server | housealice_mcp.py | 8个数据工具 | python3 housealice_mcp.py |
| 回测框架 | housealice_backtest.py | 历史验证 | python3 housealice_backtest.py |
| 风险模型 | housealice_risk.py | 风险量化评分 | python3 housealice_risk.py |
| 估值模型 | housealice_valuation.py | 房产估值 | python3 housealice_valuation.py |

### 1.2 数据组件

| 组件 | 文件 | 功能 |
|------|------|------|
| 城市数据拉取 | fetch_cities.py | 拉取63城数据 |
| 全量分析 | mega_analysis.py | 生成全量报告 |
| 市场择时 | market_timing.py | 择时信号系统 |
| 周期预测 | cycle_prediction.py | 周期预测模型 |
| 自动更新 | auto_update.py | 一键更新所有 |
| 数据管线 | data_analysis.py | 数据清洗 |

### 1.3 报告组件

| 报告 | 文件 | 内容 |
|------|------|------|
| 仪表板 | HOUSEALICE_WEB.html | Web UI |
| 仪表板 | HOUSEALICE_DASHBOARD.md | 文本仪表板 |
| 快速参考 | QUICK_REFERENCE.md | 打印贴墙上 |
| 深度审计 | DEEP_AUDIT.md | 矛盾/漏洞/升级 |
| 统一标准 | UNIFIED_STANDARDS.md | 消除矛盾 |

---

## 二、使用指南

### 2.1 日常使用

```bash
# 查看仪表板
python3 housealice_main.py

# 查看预警
python3 housealice_alert.py

# 查看决策信号
python3 housealice_decision.py

# 查看风险评分
python3 housealice_risk.py
```

### 2.2 管理房产

```python
from housealice_uha import UnifiedHousingAccount

uha = UnifiedHousingAccount("我的房产")

# 添加房产
uha.add_property(
    city="长春", district="南关", address="XXX小区",
    buy_price=80, buy_date="2018-06-01", area=90,
    floor=10, orientation="南", decoration="精装",
)
uha.properties[-1].annual_rent = 2.4  # 年租金2.4万

# 更新价值(根据最新环比)
uha.update_values({"长春": 95.9})

# 查看报告
print(uha.summary())

# 保存
uha.save()
```

### 2.3 使用MCP工具

```python
from housealice_mcp import HouseAliceMCP

mcp = HouseAliceMCP()

# 获取城市数据
data = mcp.call_tool('housing_get_city_data', city='广州')

# 获取买房信号
signal = mcp.call_tool('housing_get_buy_signal', city='广州')

# 获取卖房信号
signal = mcp.call_tool('housing_get_sell_signal', city='广州')

# 获取领先指标
leading = mcp.call_tool('housing_get_leading_indicator')

# 获取投资排名
ranking = mcp.call_tool('housing_get_investment_ranking')

# 获取季节性模式
seasonal = mcp.call_tool('housing_get_seasonal_pattern', city='广州')
```

### 2.4 自动更新

```bash
# 一键更新所有数据和报告
python3 auto_update.py

# 或者设置定时任务(每月20日)
# 已通过 cron job 设置
```

---

## 三、维护指南

### 3.1 数据更新

| 数据 | 频率 | 方法 |
|------|------|------|
| 房价指数 | 月度(每月15日) | python3 fetch_cities.py |
| 宏观指标 | 月度 | python3 data_analysis.py |
| 建材指数 | 日度 | 自动更新 |
| 报告 | 月度 | python3 auto_update.py |

### 3.2 模型更新

| 模型 | 频率 | 方法 |
|------|------|------|
| 风险评分 | 月度 | python3 housealice_risk.py |
| 回测 | 季度 | python3 housealice_backtest.py |
| 估值 | 按需 | python3 housealice_valuation.py |

### 3.3 故障排除

| 问题 | 解决方案 |
|------|---------|
| 数据拉取失败 | 检查网络/代理 |
| 报告为空 | 检查数据文件是否存在 |
| 预警不触发 | 检查阈值设置 |
| 决策信号异常 | 检查数据质量 |

---

## 四、版本历史

| 版本 | 日期 | 内容 |
|------|------|------|
| v1.0 | 2026-06-14 | 初版: 63城数据+8组件+88报告 |

---

## 五、待优化

| 任务 | 优先级 | 状态 |
|------|--------|------|
| 接入贝壳成交数据 | P0 | ⏳待做 |
| 接入贝壳租金数据 | P0 | ⏳待做 |
| ARIMA时间序列模型 | P1 | ⏳待做 |
| 历史回测完善 | P1 | ⏳待做 |
| Web UI(React) | P2 | ⏳待做 |
| SQLite数据库 | P2 | ⏳待做 |

---

*组件清单 | 2026-06-14*
