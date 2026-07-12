> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | `actionable: false`  
> 本文件来自已退役的原 HouseAlice 原型，仅保留旧研究过程，不属于 DwellProof 产品。内容未经标的、产权、税费、贷款及成交证据核验，可能错误或过期，不得用于买卖、估值、预测、排名或风险判断。DwellProof 入口：`../web/`。

# 📋 地产中介分析系统 — 完整目录

> MAGI v1.0 | 2026-06-14 | 115+文件 | 2.8MB

---

## 一、核心报告

| 报告 | 内容 | 大小 |
|------|------|------|
| EXECUTIVE_SUMMARY.md | 执行摘要(入口) | 3.6KB |
| MAGI_PROTOCOL.md | MAGI协议v1.0 | 2.7KB |
| FINAL_REPORT_v2.md | MAGI综合报告 | 7.9KB |
| MEGA_REPORT.md | 63城全量分析 | 8.5KB |

## 二、卖房决策(10城)

| 报告 | 城市 | 关键结论 |
|------|------|---------|
| GUANGZHOU_SELL_GUIDE.md | 广州 | 环比100.2🟢可卖，3月最佳 |
| SELL_GUIDE_上海.md | 上海 | 环比100.7🟢最强 |
| SELL_GUIDE_北京.md | 北京 | 环比100.4🟢可卖 |
| SELL_GUIDE_武汉.md | 武汉 | 环比100.1🟢可卖，同比最弱 |
| SELL_GUIDE_杭州.md | 杭州 | 环比99.9🟡观望 |
| SELL_GUIDE_成都.md | 成都 | 环比99.9🟡观望 |
| SELL_GUIDE_郑州.md | 郑州 | 环比99.9🟡观望 |
| SELL_GUIDE_西安.md | 西安 | 环比100.4🟢可卖 |
| SELL_GUIDE_长春.md | 长春 | 环比99.8🟡观望 |
| SELL_GUIDE_KNOWLEDGE_BASE.md | 知识库 | 16题FAQ |

## 三、市场分析

| 报告 | 内容 |
|------|------|
| MARKET_TIMING_MODEL.md | 跨城市联动+择时信号 |
| CYCLE_PREDICTION_MODEL.md | 周期预测模型 |
| HISTORY_CYCLE_INVEST.md | 历史周期+投资框架 |
| CHINA_JAPAN_COMPARISON.md | 中日对比深度 |
| INTERNATIONAL_COMPARISON.md | 全球对比+投资组合 |
| FULL_CITY_RANKING.md | 63城排名 |
| full_analysis_report.md | 数据分析报告 |

## 四、投资决策

| 报告 | 内容 |
|------|------|
| INVESTMENT_RETURN_MODEL.md | 买房vs租房vs理财 |
| BUYER_GUIDE.md | 买房决策指南 |
| MORTGAGE_RENTAL_DEVELOPER.md | 房贷+租赁+房企 |
| RISK_TAX_FUTURE.md | 风险+房产税+未来10年 |

## 五、专业知识

| 报告 | 内容 |
|------|------|
| SCHOOL_POPULATION_INFRA.md | 学区+人口+基建+区域 |
| POLICY_TAX_CONTRACT.md | 政策+税费+签约+贷款 |
| GLOSSARY.md | 术语表 |
| R3_policy_tracking.md | 政策追踪 |
| R3_lead_lag_analysis.md | 领先滞后分析 |
| R3_coal_housing_link.md | 煤价-房价联动 |

## 六、MAGI辩论产出

| 报告 | 角色 | 阶段 |
|------|------|------|
| R1_hm_analysis.md | hm | R1独立分析 |
| R1_cc_analysis.md | cc | R1独立分析 |
| R1_mc_analysis.md | mc | R1独立分析 |
| R2_hm_review.md | hm | R2交叉审 |
| R2_cc_review.md | cc | R2交叉审 |
| R2_mc_review.md | mc | R2交叉审 |
| R3_final_verdict.md | hm | R3终裁 |
| R2_round2_gz_deep.md | cc | 广州深度 |
| R2_round2_coal_link.md | mc | 煤价联动 |
| coal-housing-analysis.md | mc | 煤价详细 |

## 七、仪表板

| 文件 | 内容 |
|------|------|
| DASHBOARD_10CITY.html | 10城卖房决策板 |
| dashboard_full.html | 63城全量板 |
| dashboard.html | 基础板 |

## 八、数据

| 文件 | 内容 | 大小 |
|------|------|------|
| 70city_expanded.csv | 63城×184月 | 627KB |
| 70city_full.csv | 42城×184月 | 364KB |
| construction_index.csv | 建材指数(日度) | 324KB |
| construction_price.csv | 建材价格(日度) | 390KB |
| lpr.csv | LPR利率 | 40KB |
| m2.csv | M2货币 | 22KB |
| gdp/cpi/pmi | 宏观指标 | ~30KB |
| city_*.csv | 26个三线城市 | ~230KB |

## 九、代码

| 文件 | 功能 |
|------|------|
| mega_analysis.py | 全量分析(入口) |
| monitoring.py | 自动监测 |
| market_timing.py | 市场择时 |
| cycle_prediction.py | 周期预测 |
| batch_sell_guides.py | 批量卖房指南 |
| gz_sell_guide.py | 广州深度 |
| housing_monitor.sh | 自动化脚本 |
| fetch_cities.py | 数据拉取 |
| data_analysis.py | 数据管线 |
| full_analysis.py | 全量分析 |
| history_cycle_invest.py | 历史周期 |
| full_city_ranking.py | 城市排名 |

---

## 十、关键结论速查

### 卖房
```
最佳卖房月: 3月(所有城市一致)
当前信号: 一线🟢可卖，二线🟡观望
定价策略: 同小区成交价×0.97
议价空间: 留5-8%
```

### 买房
```
自住: 现在就买(利率3.2%+首付15%)
投资: 二三线租售比更高(2.5-3.3%)
最佳投资: 长春(3.3%)+成都(2.8%)+郑州(2.9%)
最差投资: 深圳(1.5%)+北京(1.7%)
```

### 预测
```
2026H2全国同比: 约-3%
同比转正: 一线2027-2028，二三线2029-2030
未来10年: 一线年化1-2%，三线年化-0.5%
不会崩盘: 城镇化率66%仍有10pp空间
```

---

*完整目录 | MAGI v1.0 | 2026-06-14*
