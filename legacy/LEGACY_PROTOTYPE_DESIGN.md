> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | `actionable: false`  
> 本文件来自已退役的原 HouseAlice 原型，仅保留旧研究过程，不属于 DwellProof 产品。内容未经标的、产权、税费、贷款及成交证据核验，可能错误或过期，不得用于买卖、估值、预测、排名或风险判断。DwellProof 入口：`../web/`。

# 🏠 HouseAlice — AI驱动的地产监测决策平台

> 借鉴 OpenAlice 架构 | MAGI v1.0 | 2026-06-14

---

## 一、设计哲学

OpenAlice 是"一个人的华尔街"，HouseAlice 是**"一个人的地产中介"**。

```
OpenAlice:  股票/crypto → 研究 → 下单 → 持仓管理 → 卖出
HouseAlice: 房价数据 → 分析 → 买/卖建议 → 持有监测 → 时机判断
```

核心差异：
- 股票可以秒买秒卖，房子需要数月交易
- 股票有实时行情，房价只有月度数据
- 股票是金融资产，房子是居住+资产双重属性
- 股票交易成本低，房子交易成本高(税费/中介费)

---

## 二、架构设计（借鉴OpenAlice）

### 2.1 OpenAlice 架构

```
┌─────────────────────────────────────┐
│  Surfaces (用户交互层)               │
│  ├── Web UI                         │
│  ├── Inbox (推送通道)                │
│  └── MCP Server (工具暴露)          │
├─────────────────────────────────────┤
│  Core (核心层)                       │
│  ├── Workspace (任务目录+终端)       │
│  ├── Event Log (事件日志)            │
│  ├── Cron Engine (定时任务)          │
│  └── Entity Store (状态存储)         │
├─────────────────────────────────────┤
│  Domain (领域层)                     │
│  ├── Market Data (行情数据)          │
│  ├── Analysis (技术分析)             │
│  ├── News (新闻/RSS)                │
│  └── Trading (交易执行)              │
├─────────────────────────────────────┤
│  Services (服务层)                   │
│  └── UTA (统一交易账户)              │
└─────────────────────────────────────┘
```

### 2.2 HouseAlice 架构

```
┌─────────────────────────────────────┐
│  Surfaces (用户交互层)               │
│  ├── Web UI (仪表板)                │
│  ├── Inbox (预警推送)                │
│  └── MCP Server (数据/工具暴露)     │
├─────────────────────────────────────┤
│  Core (核心层)                       │
│  ├── Workspace (分析任务目录)        │
│  ├── Event Log (数据变更日志)        │
│  ├── Cron Engine (月度监测)          │
│  └── Entity Store (房产/城市状态)    │
├─────────────────────────────────────┤
│  Domain (领域层)                     │
│  ├── Housing Data (房价数据)         │
│  ├── Macro Data (宏观数据)           │
│  ├── Policy Tracker (政策追踪)       │
│  └── Decision Engine (决策引擎)      │
├─────────────────────────────────────┤
│  Services (服务层)                   │
│  ├── UHA (统一房产账户)              │
│  ├── MAGI Engine (三角色辩论)        │
│  └── Alert Engine (预警引擎)         │
└─────────────────────────────────────┘
```

---

## 三、核心模块

### 3.1 Housing Data（房价数据层）

借鉴 OpenAlice 的 Market Data 模块：

| OpenAlice | HouseAlice | 说明 |
|-----------|-----------|------|
| 股票行情 | 70城房价指数 | 月度更新 |
| K线数据 | 同比/环比序列 | 184个月 |
| 技术指标 | Regime/趋势/波动率 | 自定义 |
| 基本面 | 宏观指标(LPR/PMI/CPI) | 月度 |
| 新闻/RSS | 政策公告/地方政策 | 实时 |

```python
# 数据源
data_sources = {
    "housing": "akshare → 国家统计局70城",
    "macro": "akshare → GDP/CPI/PMI/LPR/M2",
    "construction": "akshare → 建材指数",
    "policy": "web_search → 政策公告",
    "news": "RSS → 房地产新闻",
}
```

### 3.2 Decision Engine（决策引擎）

借鉴 OpenAlice 的 Trading 模块：

| OpenAlice | HouseAlice | 说明 |
|-----------|-----------|------|
| 买入信号 | 买房建议 | 基于Regime+环比+同比 |
| 卖出信号 | 卖房建议 | 基于Regime+环比+同比 |
| 仓位管理 | 持有监测 | 跟踪房产价值变化 |
| 止损 | 风险预警 | 跌幅预警/政策风险 |
| 止盈 | 卖出时机 | 环比转正+季节性 |

```python
# 决策规则
def buy_signal(city):
    """买房信号"""
    mom = get_latest_mom(city)  # 环比
    yoy = get_latest_yoy(city)  # 同比
    regime = get_regime(city)    # Regime
    season = get_season()        # 季节性
    
    if mom >= 100.0 and regime in ['R3', 'R1']:
        return "🟢 可以买入"
    elif mom >= 99.8:
        return "🟡 接近底部，再等等"
    else:
        return "🔴 还在下跌，不要买"

def sell_signal(city):
    """卖房信号"""
    mom = get_latest_mom(city)
    season = get_season()
    
    if mom >= 100.0 and season == "小阳春":
        return "🔥 最佳卖房窗口"
    elif mom >= 100.0:
        return "🟢 可以卖"
    elif mom >= 99.8:
        return "🟡 再等等"
    else:
        return "🔴 别卖"
```

### 3.3 UHA（统一房产账户）

借鉴 OpenAlice 的 UTA（统一交易账户）：

| OpenAlice UTA | HouseAlice UHA | 说明 |
|--------------|---------------|------|
| 多券商账户 | 多城市房产 | 统一视图 |
| 持仓汇总 | 房产组合 | 总价值/总收益 |
| 交易记录 | 买卖记录 | 成本/收益 |
| 权益曲线 | 房产价值曲线 | 跟踪变化 |
| 风险暴露 | 城市/区域集中度 | 分散风险 |

```python
# UHA 数据结构
class UnifiedHousingAccount:
    """统一房产账户"""
    def __init__(self):
        self.properties = []  # 房产列表
        self.watchlist = []   # 关注列表
    
    def add_property(self, city, district, buy_price, buy_date):
        """添加房产"""
        self.properties.append({
            'city': city,
            'district': district,
            'buy_price': buy_price,
            'buy_date': buy_date,
            'current_value': self.get_current_value(city, district),
        })
    
    def total_value(self):
        """总价值"""
        return sum(p['current_value'] for p in self.properties)
    
    def total_return(self):
        """总收益"""
        return sum(
            p['current_value'] - p['buy_price'] 
            for p in self.properties
        )
    
    def risk_exposure(self):
        """风险暴露"""
        by_city = {}
        for p in self.properties:
            by_city[p['city']] = by_city.get(p['city'], 0) + p['current_value']
        return by_city
```

### 3.4 MAGI Engine（三角色辩论引擎）

借鉴 OpenAlice 的多 Agent 架构：

| OpenAlice | HouseAlice | 说明 |
|-----------|-----------|------|
| 单Agent | MAGI三角色 | hm/cc/mc |
| 研究→交易 | 数据→分析→决策 | 三轮辩论 |
| 历史回测 | 历史验证 | 领先滞后验证 |

```python
# MAGI 引擎
class MAGIEngine:
    """MAGI 三角色辩论引擎"""
    
    def R1_independent(self, data):
        """R1: 三方独立分析"""
        hm_result = self.hm_analyze(data)
        cc_result = self.cc_analyze(data)
        mc_result = self.mc_analyze(data)
        return hm_result, cc_result, mc_result
    
    def R2_cross_review(self, r1_results):
        """R2: 交叉审"""
        hm, cc, mc = r1_results
        # cc 审 hm
        cc_review_hm = self.cc_review(cc, hm)
        # mc 审 hm
        mc_review_hm = self.mc_review(mc, hm)
        # hm 审 cc
        hm_review_cc = self.hm_review(hm, cc)
        return cc_review_hm, mc_review_hm, hm_review_cc
    
    def R3_adjudication(self, r1_results, r2_reviews):
        """R3: 终裁"""
        return self.hm_adjudicate(r1_results, r2_reviews)
```

### 3.5 Alert Engine（预警引擎）

借鉴 OpenAlice 的 Inbox：

| OpenAlice | HouseAlice | 说明 |
|-----------|-----------|------|
| 交易提醒 | 房价预警 | 环比变化 |
| 持仓警报 | 风险预警 | 跌幅/政策 |
| 新闻推送 | 政策推送 | 政策变化 |
| 定时报告 | 月度报告 | 自动化 |

```python
# 预警规则
alert_rules = {
    "shanghai_mom_above_100": {
        "condition": lambda: get_mom("上海") >= 100.0,
        "message": "🟢 上海二手房环比转正，全国2-5月后跟涨",
        "level": "info",
    },
    "city_mom_below_99": {
        "condition": lambda city: get_mom(city) < 99.0,
        "message": "🔴 {city} 二手房环比跌破99，加速下跌",
        "level": "critical",
    },
    "national_index_below_90": {
        "condition": lambda: get_national_index() < 90,
        "message": "⚠️ 国房景气指数跌破90，系统性风险",
        "level": "warning",
    },
}
```

---

## 四、技术栈（借鉴OpenAlice）

| 组件 | OpenAlice | HouseAlice | 说明 |
|------|----------|-----------|------|
| 前端 | React + Vite | React + Vite | 仪表板 |
| 后端 | Node.js + TypeScript | Python + FastAPI | 数据处理 |
| 数据库 | 文件系统(无DB) | SQLite + CSV | 轻量 |
| AI | Claude/Codex/PI | mimo-v2.5-pro | MAGI引擎 |
| MCP | MCP Server | MCP Server | 工具暴露 |
| 定时 | Cron Engine | Cron Engine | 月度监测 |
| 推送 | Inbox | Inbox | 预警推送 |

---

## 五、功能对比

| 功能 | OpenAlice | HouseAlice | 状态 |
|------|----------|-----------|------|
| 数据采集 | ✅ 实时行情 | ✅ 月度房价 | 已实现 |
| 技术分析 | ✅ K线/指标 | ✅ Regime/趋势 | 已实现 |
| 基本面 | ✅ 财务报表 | ✅ 宏观指标 | 已实现 |
| 决策引擎 | ✅ 买卖信号 | ✅ 买/卖建议 | 已实现 |
| 多Agent | ❌ 单Agent | ✅ MAGI三角色 | 已实现 |
| 历史验证 | ✅ 回测 | ✅ 领先滞后验证 | 已实现 |
| 预警系统 | ✅ 交易提醒 | ✅ 房价预警 | 已实现 |
| 仪表板 | ✅ Web UI | ✅ HTML | 已实现 |
| 自动化 | ✅ Cron | ✅ Cron | 已实现 |
| UTA/UHA | ✅ 统一账户 | ⏳ 待实现 | 计划中 |
| MCP Server | ✅ | ⏳ 待实现 | 计划中 |
| Inbox | ✅ | ⏳ 待实现 | 计划中 |

---

## 六、与地产中介分析系统的集成

```
现有系统(~/DEVELOPMENT/quinte-housing/)
├── 数据层: 63城×184月 CSV
├── 分析层: 80个MD报告
├── 代码层: 13个Python脚本
├── 仪表板: 3个HTML
└── 自动化: Cron job

HouseAlice(新项目)
├── 继承: 所有数据和分析
├── 新增: UHA统一房产账户
├── 新增: MCP Server
├── 新增: Inbox预警推送
├── 新增: Web UI(React)
└── 新增: MAGI引擎集成
```

---

## 七、开发路线图

### Phase 1: MVP (1周)
- [x] 数据采集(akshare)
- [x] 分析引擎(Python)
- [x] 仪表板(HTML)
- [x] 自动化(Cron)
- [ ] UHA统一房产账户
- [ ] 预警引擎

### Phase 2: 产品化 (2周)
- [ ] Web UI(React)
- [ ] MCP Server
- [ ] Inbox推送
- [ ] 更多城市数据

### Phase 3: 智能化 (4周)
- [ ] MAGI引擎集成
- [ ] 自然语言查询
- [ ] 个性化建议
- [ ] 社区功能

---

## 八、关键结论

1. **OpenAlice 架构可借鉴**: Workspace + MCP + Inbox + Cron
2. **核心差异**: 房子是慢资产(月度数据+数月交易)
3. **已有基础**: 数据+分析+仪表板+自动化已完备
4. **新增模块**: UHA + MCP + Inbox + Web UI
5. **开发成本**: MVP 1周，产品化 2周，智能化 4周

---

*HouseAlice | 借鉴OpenAlice | MAGI v1.0 | 2026-06-14*
