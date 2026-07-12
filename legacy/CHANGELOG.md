> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | `actionable: false`  
> 本文件来自已退役的原 HouseAlice 原型，仅保留旧研究过程，不属于 DwellProof 产品。内容未经标的、产权、税费、贷款及成交证据核验，可能错误或过期，不得用于买卖、估值、预测、排名或风险判断。DwellProof 入口：`../web/`。

# 📝 HouseAlice 版本日志

> 2026-06-14

---

## v1.0 (2026-06-14) — 初始版本

### 新增功能
- 63城房价数据(akshare)
- 85个MD分析报告
- MAGI三角色辩论系统(hm+cc+mc)
- HouseAlice 8大组件
- Web UI仪表板
- 自动监测Cron Job

### HouseAlice组件
- housealice_main.py — 统一入口
- housealice_uha.py — 统一房产账户
- housealice_alert.py — 预警引擎
- housealice_decision.py — 决策引擎
- housealice_mcp.py — MCP Server
- housealice_backtest.py — 回测框架
- housealice_risk.py — 风险模型
- housealice_valuation.py — 估值模型

### 数据覆盖
- 63城 × 184月(2011-2026)
- 宏观: GDP/CPI/PMI/LPR/M2
- 建材指数(日度)
- 期货: 动力煤/焦煤/螺纹钢/玻璃

### 分析报告
- 10城卖房指南
- 63城全量分析
- 市场择时信号系统
- 周期预测模型
- 历史周期对比
- 中日对比
- 国际对比
- 投资回报测算
- 买房决策指南
- 房贷计算器
- 税费计算器
- 政策时间线
- 法律/产权/纠纷
- 学区/人口/基建
- 房企/租赁/商业
- 风险/房产税/未来10年
- 购房心理/装修/物业
- 教育/医疗/交通
- 养老/海外/保险
- 科技/智能/绿色
- 粤港澳大湾区
- 煤价-房价联动
- 宏观经济分析
- 谈判心理战
- 产业链+城市竞争力
- 人口+老龄化+城镇化
- 金融风险+银行+地方财政
- 能源转型+碳中和+绿色建筑
- 数字经济+远程办公+元宇宙
- 各城市深度分析(8城)

### 回测结果
- 领先指标准确率: 65.4%
- 买房信号准确率: 46-68%
- 卖房信号准确率: 70-85%

### 长春专项
- 长春深度分析
- 长春卖房策略
- 长春多套房决策树

---

## v1.1 (计划中)

### 待优化
- 接入贝壳成交数据
- 接入贝壳租金数据
- ARIMA时间序列模型
- 历史回测完善
- Web UI(React)
- SQLite数据库
- 更多城市数据

---

*版本日志 | 2026-06-14*
