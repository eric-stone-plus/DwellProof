> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | `actionable: false`  
> 本文件来自已退役的原 HouseAlice 原型，仅保留旧研究过程，不属于 DwellProof 产品。内容未经标的、产权、税费、贷款及成交证据核验，可能错误或过期，不得用于买卖、估值、预测、排名或风险判断。DwellProof 入口：`../web/`。

TASK: 你是 mc（宏观经济学家），构建房价预测模型。

读取: /tmp/quinte-housing/70city_full.csv（42城184月完整数据）
读取: /tmp/quinte-housing/lpr.csv
读取: /tmp/quinte-housing/pmi.csv

用Python构建以下模型：

## 1. 时间序列模型
- ARIMA/SARIMA: 对北京/上海/广州/深圳的二手房同比序列建模
- 滚动回测: 用2011-2024训练, 2025-2026测试
- 输出: MAPE, 方向准确率, 6步预测

## 2. 特征工程
- 滞后特征: 1/3/6/12月滞后
- 动量特征: 3/6月移动平均
- 宏观特征: LPR, PMI
- 交叉特征: 城市间领先滞后关系

## 3. 回测评估
- 训练集: 2011-2024
- 测试集: 2025-2026
- 指标: MAPE, RMSE, 方向准确率

## 4. 2026H2预测
- 每个城市给出点预测+置信区间
- 识别哪些城市预测最不确定

用Python代码实际计算，输出代码+结果。
