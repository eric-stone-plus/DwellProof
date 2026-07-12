#!/usr/bin/env python3
"""
退役原型 — 决策引擎 (Decision Engine)
借鉴 OpenAlice 的 Trading 模块
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List

OUTPUT = Path(__file__).resolve().parent


class DecisionEngine:
    """决策引擎"""
    
    def __init__(self):
        self.rules = self.setup_rules()
    
    def setup_rules(self):
        """保留旧接口，但停用仅依赖城市指数的方向性规则。"""
        return {}

    @staticmethod
    def _market_context(data: Dict) -> Dict:
        """把城市指数转换为描述性背景，不转换为交易动作。"""
        mom = data.get('mom')
        if not isinstance(mom, (int, float)):
            return {
                'signal': '⚪ 市场背景数据不足',
                'reason': '缺少可用的城市二手住宅环比指数',
            }
        if mom >= 100.0:
            description = '城市二手住宅价格指数环比不低于100'
        elif mom >= 99.5:
            description = '城市二手住宅价格指数环比低于100但接近持平'
        else:
            description = '城市二手住宅价格指数环比低于99.5'
        return {'signal': 'ℹ️ 仅市场背景', 'reason': description}
    
    def analyze(self, city: str, data: Dict) -> Dict:
        """分析单个城市"""
        missing = [
            field for field in (
                'comparable_sales', 'annual_rent', 'total_acquisition_cost',
                'legal_due_diligence', 'financing_cost',
            )
            if data.get(field) in (None, '', [], {})
        ]
        reason = (
            '城市价格指数不能单独支持买入、卖出或持有决策；'
            f"缺少标的级证据: {', '.join(missing)}"
            if missing
            else '旧规则未经净收益和真实成交回测，方向性决策已停用'
        )
        insufficient = {
            'signal': '⚪ 证据不足',
            'reason': reason,
            'rule': 'legacy_city_signal_disabled',
            'actionable': False,
        }
        result = {
            'city': city,
            'timestamp': datetime.now().isoformat(),
            'data': data,
            'decision_status': 'insufficient_evidence',
            'missing_evidence': missing,
            'market_context': self._market_context(data),
            'signals': {
                action: dict(insufficient) for action in ('buy', 'sell', 'hold')
            },
        }
        return result
    
    def analyze_all(self, city_data: Dict[str, Dict]) -> List[Dict]:
        """分析所有城市"""
        results = []
        for city, data in city_data.items():
            if city.startswith('_'):
                continue
            result = self.analyze(city, data)
            results.append(result)
        return results
    
    def format_report(self, results: List[Dict]) -> str:
        """Render compatibility refusals without recommendation headings."""
        r = [
            "> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | "
            "`actionable: false`  ",
            "> 本文件来自已退役的原 HouseAlice 原型，不属于 DwellProof。内容未经标的、产权、"
            "税费、贷款及成交证据核验，不得用于买卖、估值、预测、排名或风险判断。"
            "DwellProof 入口：`../web/`。\n",
        ]
        r.append("# 退役原型旧决策接口拒答报告\n")
        r.append(f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        r.append("> `INSUFFICIENT_EVIDENCE` | `actionable: false`")
        r.append("\n## 城市指数背景与拒答原因\n")
        r.append("| 城市 | 环比 | 同比 | 状态 | 原因 |")
        r.append("|------|------|------|------|------|")
        for res in results:
            buy = res['signals'].get('buy', {})
            data = res['data']
            r.append(
                f"| {res['city']} | {data.get('mom', 0):.1f} | "
                f"{data.get('yoy', 0):.1f} | {buy.get('signal', '—')} | "
                f"{buy.get('reason', '—')} |"
            )
        
        return "\n".join(r)


def demo():
    """演示"""
    print("=" * 60)
    print("  退役原型 — 决策引擎 Demo")
    print("=" * 60)
    
    engine = DecisionEngine()
    
    # 模拟数据
    city_data = {
        '上海': {'mom': 100.7, 'yoy': 94.4, 'regime': 'R3', 'trend': 0.5, 'season': datetime.now().month},
        '北京': {'mom': 100.4, 'yoy': 92.6, 'regime': 'R3', 'trend': 0.3, 'season': datetime.now().month},
        '广州': {'mom': 100.2, 'yoy': 92.1, 'regime': 'R3', 'trend': 0.2, 'season': datetime.now().month},
        '深圳': {'mom': 100.3, 'yoy': 93.5, 'regime': 'R3', 'trend': 0.3, 'season': datetime.now().month},
        '武汉': {'mom': 100.1, 'yoy': 90.6, 'regime': 'R3', 'trend': 0.1, 'season': datetime.now().month},
        '杭州': {'mom': 99.9, 'yoy': 95.0, 'regime': 'R2', 'trend': 0.1, 'season': datetime.now().month},
        '成都': {'mom': 99.9, 'yoy': 93.9, 'regime': 'R2', 'trend': 0.1, 'season': datetime.now().month},
        '郑州': {'mom': 99.9, 'yoy': 92.2, 'regime': 'R2', 'trend': 0.0, 'season': datetime.now().month},
        '西安': {'mom': 100.4, 'yoy': 91.9, 'regime': 'R3', 'trend': 0.4, 'season': datetime.now().month},
        '长春': {'mom': 99.8, 'yoy': 95.9, 'regime': 'R2', 'trend': 0.0, 'season': datetime.now().month},
    }
    
    results = engine.analyze_all(city_data)
    report = engine.format_report(results)
    print(report)
    
    with open(OUTPUT / "DECISION_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n报告已保存: {OUTPUT / 'DECISION_REPORT.md'}")


if __name__ == "__main__":
    demo()
