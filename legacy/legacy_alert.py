#!/usr/bin/env python3
"""Legacy market-context review prompts; never transaction alerts."""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Callable

OUTPUT = Path(__file__).resolve().parent
INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class Alert:
    """单个预警"""
    def __init__(self, name: str, level: str, message: str, 
                 condition_desc: str, city: str = ""):
        self.name = name
        self.level = level  # info/warning/critical
        self.message = message
        self.condition_desc = condition_desc
        self.city = city
        self.triggered_at = datetime.now().isoformat()
        self.acknowledged = False
        self.status = INSUFFICIENT_EVIDENCE
        self.actionable = False
    
    def to_dict(self):
        return {
            'name': self.name,
            'level': self.level,
            'message': self.message,
            'condition_desc': self.condition_desc,
            'city': self.city,
            'triggered_at': self.triggered_at,
            'acknowledged': self.acknowledged,
            'status': self.status,
            'actionable': self.actionable,
            'role': 'market_context_review',
        }


class AlertEngine:
    """预警引擎"""
    
    def __init__(self):
        self.rules: List[Dict] = []
        self.history: List[Alert] = []
        self.setup_default_rules()
    
    def setup_default_rules(self):
        """设置默认预警规则"""
        
        # Shanghai is retained as an observation only, not a national predictor.
        self.add_rule(
            name="上海环比观察值不低于100",
            level="info",
            message=(
                "上海二手住宅价格指数环比为 {shanghai_mom:.1f}；"
                "仅记录城市市场背景，请人工核验官方观察期和口径，"
                "不得推导其他城市或标的交易动作"
            ),
            condition=lambda data: data.get('shanghai_mom', 0) >= 100.0,
            condition_desc="上海二手房环比 >= 100.0",
        )
        
        self.add_rule(
            name="上海环比观察值不低于100.5",
            level="info",
            message=(
                "上海二手住宅价格指数环比为 {shanghai_mom:.1f}；"
                "触发人工核验提示，不构成市场预测或标的方向判断"
            ),
            condition=lambda data: data.get('shanghai_mom', 0) >= 100.5,
            condition_desc="上海二手房环比 >= 100.5",
        )
        
        # 城市预警
        self.add_rule(
            name="城市环比观察值低于99",
            level="critical",
            message=(
                "{city} 二手住宅价格指数环比为 {mom:.1f}；"
                "请人工核验观察期、口径和原始来源，不构成标的风险结论"
            ),
            condition=lambda data: data.get('mom', 100) < 99.0,
            condition_desc="城市二手房环比 < 99.0",
        )
        
        self.add_rule(
            name="城市同比观察值低于90",
            level="critical",
            message=(
                "{city} 二手住宅价格指数同比为 {yoy:.1f}；"
                "请人工核验观察期、口径和原始来源，不构成标的风险结论"
            ),
            condition=lambda data: data.get('yoy', 100) < 90.0,
            condition_desc="城市二手房同比 < 90.0",
        )
        
        # 全国预警
        self.add_rule(
            name="国房景气指数观察值低于90",
            level="warning",
            message=(
                "国房景气指数观察值为 {national_index:.1f}；"
                "请人工核验官方来源和观察期，不构成标的风险判断"
            ),
            condition=lambda data: data.get('national_index', 100) < 90,
            condition_desc="国房景气指数 < 90",
        )
        
        # 政策预警
        self.add_rule(
            name="LPR变动观察",
            level="info",
            message=(
                "LPR月度变动为 {lpr_change:.2f} 个百分点；"
                "LPR仅是定价基准，请人工核验银行书面执行利率"
            ),
            condition=lambda data: data.get('lpr_change', 0) < 0,
            condition_desc="LPR较上月下降",
        )
    
    def add_rule(self, name: str, level: str, message: str,
                 condition: Callable, condition_desc: str):
        """添加预警规则"""
        self.rules.append({
            'name': name,
            'level': level,
            'message': message,
            'condition': condition,
            'condition_desc': condition_desc,
        })
    
    def check(self, data: Dict) -> List[Alert]:
        """检查预警"""
        triggered = []
        for rule in self.rules:
            try:
                if rule['condition'](data):
                    alert = Alert(
                        name=rule['name'],
                        level=rule['level'],
                        message=rule['message'].format(**data),
                        condition_desc=rule['condition_desc'],
                        city=data.get('city', ''),
                    )
                    triggered.append(alert)
                    self.history.append(alert)
            except Exception as e:
                pass  # 条件检查失败，跳过
        return triggered
    
    def check_all_cities(self, city_data: Dict[str, Dict]) -> List[Alert]:
        """检查所有城市"""
        all_alerts = []
        
        # 全国级别预警
        national_alerts = self.check({
            'shanghai_mom': city_data.get('上海', {}).get('mom', 0),
            'national_index': city_data.get('_national', {}).get('index', 100),
            'lpr_change': city_data.get('_macro', {}).get('lpr_change', 0),
        })
        all_alerts.extend(national_alerts)
        
        # 城市级别预警
        for city, data in city_data.items():
            if city.startswith('_'):
                continue
            city_alerts = self.check({
                'city': city,
                'mom': data.get('mom', 100),
                'yoy': data.get('yoy', 100),
            })
            all_alerts.extend(city_alerts)
        
        return all_alerts
    
    def format_alerts(self, alerts: List[Alert]) -> str:
        """格式化预警"""
        if not alerts:
            return "无预警"
        
        r = []
        r.append(f"## 市场背景人工核验提示 ({len(alerts)}条)\n")
        
        critical = [a for a in alerts if a.level == 'critical']
        warning = [a for a in alerts if a.level == 'warning']
        info = [a for a in alerts if a.level == 'info']
        
        if critical:
            r.append("### 高优先级核验")
            for a in critical:
                r.append(f"- {a.message}")
        
        if warning:
            r.append("### 需核验")
            for a in warning:
                r.append(f"- {a.message}")
        
        if info:
            r.append("### 背景观察")
            for a in info:
                r.append(f"- {a.message}")
        
        return "\n".join(r)
    
    def save_history(self, path: str = None):
        """保存历史"""
        if path is None:
            path = f"{OUTPUT}/alert_history.json"
        data = [a.to_dict() for a in self.history]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"预警历史已保存: {path}")


def demo():
    """Refuse the synthetic demo so it cannot create apparent alert history."""
    raise SystemExit(
        "DISABLED_LEGACY_ALERT_DEMO: synthetic observations must not be "
        "written as alert history"
    )


if __name__ == "__main__":
    demo()
