> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | `actionable: false`  
> 本文件来自已退役的原 HouseAlice 原型，仅保留旧研究过程，不属于 DwellProof 产品。内容未经标的、产权、税费、贷款及成交证据核验，可能错误或过期，不得用于买卖、估值、预测、排名或风险判断。DwellProof 入口：`../web/`。

# 🏗️ HouseAlice 系统架构图

> 2026-06-14

---

## 一、整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    HouseAlice v1.0                          │
│               AI驱动的地产监测决策平台                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │  Web UI     │  │  MCP Server │  │  Cron Job   │        │
│  │  仪表板     │  │  8个工具    │  │  月度监测   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │
│  ┌──────┴────────────────┴────────────────┴──────┐        │
│  │              HouseAlice 主程序                  │        │
│  │              (housealice_main.py)               │        │
│  └──────┬────────────────┬────────────────┬──────┘        │
│         │                │                │                │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐        │
│  │  UHA        │  │  Alert      │  │  Decision   │        │
│  │  房产账户   │  │  预警引擎   │  │  决策引擎   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │
│  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐        │
│  │  Backtest   │  │  Risk       │  │  Valuation  │        │
│  │  回测框架   │  │  风险模型   │  │  估值模型   │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                │
│  ┌──────┴────────────────┴────────────────┴──────┐        │
│  │              数据层                            │        │
│  │  63城×184月 | 宏观指标 | 建材指数 | 期货       │        │
│  └───────────────────────────────────────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 二、数据流

```
数据源                处理层              输出层
──────                ──────              ──────
akshare          →   data_analysis.py →   70city_full.csv
国家统计局       →   fetch_cities.py  →   70city_expanded.csv
宏观指标         →   mega_analysis.py →   MEGA_REPORT.md
建材指数         →   market_timing.py →   MARKET_TIMING_MODEL.md
                 →   cycle_prediction →   CYCLE_PREDICTION_MODEL.md
                 →   housealice_main  →   HOUSEALICE_DASHBOARD.md
                 →   housealice_alert →   ALERT_REPORT.md
                 →   housealice_risk  →   RISK_REPORT.md
```

## 三、MAGI三角色流程

```
R1: 独立分析
├── hm(主审)  → R1_hm_analysis.md
├── cc(审查者) → R1_cc_analysis.md
└── mc(宏观)   → R1_mc_analysis.md

R2: 交叉审
├── cc审hm → R2_cc_review.md
├── mc审hm → R2_mc_review.md
└── hm审cc → R2_hm_review.md

R3: 终裁
└── hm → R3_final_verdict.md
```

## 四、HouseAlice组件交互

```
housealice_main.py
├── 调用 → housealice_uha.py (房产账户)
├── 调用 → housealice_alert.py (预警)
├── 调用 → housealice_decision.py (决策)
└── 调用 → housealice_mcp.py (工具)

housealice_mcp.py
├── get_city_data() → 70city_expanded.csv
├── get_national_summary() → 梯队汇总
├── get_buy_signal() → 买房信号
├── get_sell_signal() → 卖房信号
├── compare_cities() → 城市对比
├── get_leading_indicator() → 上海领先指标
├── get_seasonal_pattern() → 季节性模式
└── get_investment_ranking() → 投资排名

housealice_backtest.py
├── backtest_leading_indicator() → 领先指标回测
├── backtest_buy_signal() → 买房信号回测
└── backtest_sell_signal() → 卖房信号回测

housealice_risk.py
└── calculate_risk_score() → 风险评分(0-100)

housealice_valuation.py
└── estimate() → 房产估值
```

## 五、文件结构

```
~/DEVELOPMENT/quinte-housing/
├── 数据(45个CSV)
│   ├── 70city_expanded.csv (核心)
│   ├── construction_index.csv
│   ├── gdp/cpi/pmi/lpr/m2.csv
│   └── city_*.csv (26个三线城市)
│
├── 报告(95个MD)
│   ├── 核心报告(5)
│   ├── 卖房指南(11)
│   ├── 市场分析(5)
│   ├── 投资决策(5)
│   ├── 专业知识(9)
│   ├── MAGI辩论(15)
│   ├── 城市深度(8)
│   ├── HouseAlice组件(8)
│   └── 其他(29)
│
├── 代码(27个Python)
│   ├── housealice_*.py (8个组件)
│   ├── mega_analysis.py
│   ├── market_timing.py
│   ├── cycle_prediction.py
│   ├── auto_update.py
│   └── 其他(12)
│
├── 仪表板(4个HTML)
│   ├── HOUSEALICE_WEB.html
│   ├── DASHBOARD_10CITY.html
│   ├── dashboard_full.html
│   └── dashboard.html
│
└── 配置
    ├── CHANGELOG.md
    ├── COMPONENT_GUIDE.md
    ├── QUICK_REFERENCE.md
    └── UNIFIED_STANDARDS.md
```

---

*系统架构图 | 2026-06-14*
