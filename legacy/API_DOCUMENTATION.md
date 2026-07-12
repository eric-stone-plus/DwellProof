> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | `actionable: false`  
> 本文件来自已退役的原 HouseAlice 原型，仅保留旧研究过程，不属于 DwellProof 产品。内容未经标的、产权、税费、贷款及成交证据核验，可能错误或过期，不得用于买卖、估值、预测、排名或风险判断。DwellProof 入口：`../web/`。

# 📖 HouseAlice API 文档

> 2026-06-14 | 8个MCP工具

---

## 一、MCP工具列表

### 1.1 housing_get_city_data

**描述:** 获取指定城市的房价数据(同比/环比/Regime)

**输入:**
```json
{
  "city": "广州"  // 城市名称
}
```

**输出:**
```json
{
  "city": "广州",
  "date": "2026-04",
  "new_house": {
    "yoy": 95.6,  // 新房同比
    "mom": 100.1  // 新房环比
  },
  "used_house": {
    "yoy": 92.1,  // 二手同比
    "mom": 100.2  // 二手环比
  },
  "trend_6m": {
    "new_mom_avg": 99.78,  // 近6月新房环比均值
    "used_mom_avg": 99.50  // 近6月二手环比均值
  }
}
```

**示例:**
```python
from housealice_mcp import HouseAliceMCP
mcp = HouseAliceMCP()
data = mcp.call_tool('housing_get_city_data', city='广州')
```

---

### 1.2 housing_get_national_summary

**描述:** 获取全国房价汇总(梯队/区域/Regime)

**输入:** 无

**输出:**
```json
{
  "date": "2026-04",
  "total_cities": 63,
  "tiers": {
    "T1": {
      "city_count": 4,
      "new_mom_avg": 100.10,
      "used_mom_avg": 100.40,
      "new_yoy_avg": 97.9,
      "used_yoy_avg": 93.2
    },
    "T2": { ... },
    "T3": { ... }
  }
}
```

**示例:**
```python
summary = mcp.call_tool('housing_get_national_summary')
```

---

### 1.3 housing_get_buy_signal

**描述:** 获取指定城市的买房信号

**输入:**
```json
{
  "city": "广州"
}
```

**输出:**
```json
{
  "city": "广州",
  "signal": "🟢 可以买入",
  "reason": "环比转正",
  "data": { ... }
}
```

**信号类型:**
- 🟢 强烈买入: 环比≥100.5 且 Regime=R3/R1
- 🟢 可以买入: 环比≥100.0 且 Regime=R3/R1
- 🟡 接近底部: 环比≥99.8 且趋势向上
- 🟡 再等等: 环比≥99.5
- 🔴 不要买: 环比<99.5

---

### 1.4 housing_get_sell_signal

**描述:** 获取指定城市的卖房信号

**输入:**
```json
{
  "city": "广州"
}
```

**输出:**
```json
{
  "city": "广州",
  "signal": "🟢 可以卖",
  "reason": "环比转正",
  "data": { ... }
}
```

**信号类型:**
- 🔥 最佳卖房窗口: 环比≥100.0 且 3-4月
- 🟢 可以卖: 环比≥100.0
- 🟡 再等等: 环比≥99.8
- 🔴 别卖: 环比<99.5

---

### 1.5 housing_compare_cities

**描述:** 多城市房价指标对比

**输入:**
```json
{
  "cities": ["上海", "北京", "广州", "深圳"]
}
```

**输出:**
```json
{
  "上海": { ... },
  "北京": { ... },
  "广州": { ... },
  "深圳": { ... }
}
```

---

### 1.6 housing_get_leading_indicator

**描述:** 获取上海领先指标(全国领先2-5月)

**输入:** 无

**输出:**
```json
{
  "indicator": "上海二手房环比",
  "current_value": 100.7,
  "signal": "🟢 领先指标转正",
  "lead_time": "2-5个月",
  "meaning": "上海二手房环比转正后，全国2-5个月内跟涨",
  "data": { ... }
}
```

---

### 1.7 housing_get_seasonal_pattern

**描述:** 获取季节性卖房窗口

**输入:**
```json
{
  "city": "广州"
}
```

**输出:**
```json
{
  "city": "广州",
  "best_month": 3,
  "best_month_value": 100.60,
  "worst_month": 11,
  "worst_month_value": 99.84,
  "monthly": { 1: 100.12, 2: 100.32, ... }
}
```

---

### 1.8 housing_get_investment_ranking

**描述:** 获取城市投资排名(租售比+环比+同比)

**输入:** 无

**输出:**
```json
{
  "ranking": [
    {
      "rank": 1,
      "city": "长春",
      "rent_yield": 3.3,
      "mom": 99.8,
      "yoy": 95.9,
      "recommendation": "🟢 投资首选"
    },
    ...
  ]
}
```

---

## 二、使用示例

### 2.1 获取广州买房信号
```python
from housealice_mcp import HouseAliceMCP
mcp = HouseAliceMCP()
signal = mcp.call_tool('housing_get_buy_signal', city='广州')
print(f"信号: {signal['signal']}")
print(f"原因: {signal['reason']}")
```

### 2.2 比较一线城市
```python
comparison = mcp.call_tool('housing_compare_cities', cities=['上海', '北京', '广州', '深圳'])
for city, data in comparison.items():
    print(f"{city}: 新房{data['new_house']['yoy']:.1f} 二手{data['used_house']['yoy']:.1f}")
```

### 2.3 获取投资排名
```python
ranking = mcp.call_tool('housing_get_investment_ranking')
for item in ranking['ranking']:
    print(f"{item['rank']}. {item['city']}: {item['rent_yield']:.1f}% {item['recommendation']}")
```

---

*API文档 | 2026-06-14*
