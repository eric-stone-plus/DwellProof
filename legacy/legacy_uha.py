#!/usr/bin/env python3
"""
退役原型 — 统一房产账户 (UHA)
借鉴 OpenAlice 的 UTA (Unified Trading Account)
"""

import json
from datetime import datetime
from math import isfinite
from pathlib import Path
from typing import Dict, List, Optional

OUTPUT = Path(__file__).resolve().parent
INSUFFICIENT_PROPERTY_EVIDENCE = "INSUFFICIENT_PROPERTY_EVIDENCE"
MARKET_CONTEXT_WARNING = (
    "城市价格指数仅是市场背景，不能用于推算单套房当前价值或收益率"
)


class Property:
    """单个房产"""
    def __init__(self, city: str, district: str, address: str,
                 buy_price: float, buy_date: str, area: float,
                 property_type: str = "住宅", floor: int = 0,
                 orientation: str = "", decoration: str = ""):
        self.city = city
        self.district = district
        self.address = address
        self.buy_price = buy_price  # 万元
        self.buy_date = buy_date
        self.area = area  # 平方米
        self.property_type = property_type
        self.floor = floor
        self.orientation = orientation
        self.decoration = decoration
        # 当前价值必须由可追溯的房源级证据支持；买入价不是当前价值。
        self.current_value = None
        self.value_status = INSUFFICIENT_PROPERTY_EVIDENCE
        self.value_observation = None
        self.market_context: Dict[str, Dict] = {}
        self.legacy_unverified_value = None
        # The legacy schema has no rent source, observation period, or status.
        self.annual_rent = None
        self.legacy_unverified_annual_rent = None
        self.notes = []
    
    def unit_price(self):
        """Historical acquisition unit cost (万元/平方米)."""
        return self.buy_price / self.area if self.area > 0 else 0
    
    def update_value(self, city_mom: float, observation_id: str = None) -> Dict:
        """Fail closed and record a city index as market context only.

        The method name is retained for legacy callers. It never changes the
        property value. An observation id makes context recording idempotent.
        """
        if isinstance(city_mom, bool) or not isinstance(city_mom, (int, float)):
            raise ValueError("city_mom must be a finite positive number")
        if not isfinite(float(city_mom)) or city_mom <= 0:
            raise ValueError("city_mom must be a finite positive number")

        recorded = False
        duplicate = False
        conflict = False
        if observation_id:
            existing = self.market_context.get(observation_id)
            if existing is None:
                self.market_context[observation_id] = {
                    'observation_id': observation_id,
                    'city': self.city,
                    'metric': '二手住宅城市价格指数-环比',
                    'index_value': float(city_mom),
                    'unit': '上月=100',
                    'role': 'market_context',
                    'actionable': False,
                    'warning': MARKET_CONTEXT_WARNING,
                }
                self.value_observation = observation_id
                recorded = True
            else:
                duplicate = True
                conflict = existing.get('index_value') != float(city_mom)

        return {
            'status': INSUFFICIENT_PROPERTY_EVIDENCE,
            'actionable': False,
            'non_actionable': True,
            'property_value_changed': False,
            'current_value': None,
            'market_context_recorded': recorded,
            'duplicate_observation': duplicate,
            'observation_conflict': conflict,
            'observation_id': observation_id,
            'warning': MARKET_CONTEXT_WARNING,
        }

    def update_property_value(
        self, city_mom: float, observation_id: str = None
    ) -> Dict:
        """Compatibility alias for the legacy property-value update API."""
        return self.update_value(city_mom, observation_id)
    
    def return_rate(self):
        """Current-value return is unavailable without property evidence."""
        return None
    
    def rental_yield(self):
        """Current-value rental yield is unavailable without property evidence."""
        return None

    def rental_yield_on_cost(self):
        """Refuse yield because legacy rent has no evidence metadata."""
        return None
    
    def to_dict(self):
        return {
            'city': self.city,
            'district': self.district,
            'address': self.address,
            'buy_price': self.buy_price,
            'buy_date': self.buy_date,
            'area': self.area,
            'property_type': self.property_type,
            'floor': self.floor,
            'orientation': self.orientation,
            'decoration': self.decoration,
            'current_value': self.current_value,
            'value_status': self.value_status,
            'value_observation': self.value_observation,
            'market_context': self.market_context,
            'legacy_unverified_value': self.legacy_unverified_value,
            'annual_rent': self.annual_rent,
            'legacy_unverified_annual_rent': self.legacy_unverified_annual_rent,
            'notes': self.notes,
        }


class UnifiedHousingAccount:
    """统一房产账户"""
    
    def __init__(self, name: str = "我的房产组合"):
        self.name = name
        self.properties: List[Property] = []
        self.watchlist: List[Dict] = []  # 关注列表
        self.transactions: List[Dict] = []  # 交易记录
        self.created_at = datetime.now().isoformat()
    
    def add_property(self, **kwargs) -> Property:
        """添加房产"""
        p = Property(**kwargs)
        self.properties.append(p)
        self.transactions.append({
            'type': 'buy',
            'property': p.to_dict(),
            'timestamp': datetime.now().isoformat(),
        })
        return p
    
    def sell_property(self, index: int, sell_price: float) -> Dict:
        """Record a sale without mislabelling gross price spread as profit."""
        if isinstance(index, bool) or not isinstance(index, int):
            return {'error': '索引必须为非负整数'}
        if index < 0 or index >= len(self.properties):
            return {'error': '索引超出范围'}
        if (
            isinstance(sell_price, bool)
            or not isinstance(sell_price, (int, float))
            or not isfinite(float(sell_price))
            or sell_price <= 0
        ):
            return {'error': '成交价必须为有限正数'}
        
        p = self.properties[index]
        gross_price_spread = sell_price - p.buy_price
        
        result = {
            'city': p.city,
            'district': p.district,
            'buy_price': p.buy_price,
            'sell_price': sell_price,
            'gross_price_spread': gross_price_spread,
            'profit': None,
            'profit_rate': None,
            'status': 'INSUFFICIENT_FULL_COST_EVIDENCE',
            'actionable': False,
            'warning': '未提供税费、融资、持有和退出成本，不计算利润或收益率',
            'hold_period': (datetime.now() - datetime.fromisoformat(p.buy_date)).days,
        }
        
        self.transactions.append({
            'type': 'sell',
            'result': result,
            'timestamp': datetime.now().isoformat(),
        })
        
        self.properties.pop(index)
        return result
    
    def add_watchlist(self, city: str, district: str, reason: str = ""):
        """添加关注"""
        self.watchlist.append({
            'city': city,
            'district': district,
            'reason': reason,
            'added_at': datetime.now().isoformat(),
        })
    
    def total_value(self) -> Optional[float]:
        """Legacy records cannot satisfy the new property-evidence contract."""
        return 0.0 if not self.properties else None
    
    def total_cost(self) -> float:
        """总成本(万元)"""
        return sum(p.buy_price for p in self.properties)
    
    def total_return(self) -> Optional[float]:
        """Return unrealized gain only when current values are verified."""
        value = self.total_value()
        return value - self.total_cost() if value is not None else None
    
    def total_return_rate(self) -> Optional[float]:
        """Return current-value return rate only with verified values."""
        cost = self.total_cost()
        total_return = self.total_return()
        if total_return is None:
            return None
        return total_return / cost * 100 if cost > 0 else 0
    
    def total_rental_income(self) -> Optional[float]:
        """Legacy rent lacks provenance, so no portfolio total is available."""
        return 0.0 if not self.properties else None
    
    def total_rental_yield(self) -> Optional[float]:
        """Return current-value rental yield only with verified values."""
        value = self.total_value()
        income = self.total_rental_income()
        if value is None or income is None:
            return None
        return income / value * 100 if value > 0 else 0

    def total_rental_yield_on_cost(self) -> Optional[float]:
        """Refuse yield because legacy rent has no evidence metadata."""
        return None
    
    def risk_exposure(self) -> Dict:
        """Acquisition-cost exposure by city; this is not market value."""
        by_city = {}
        for p in self.properties:
            by_city[p.city] = by_city.get(p.city, 0) + p.buy_price
        total = self.total_cost()
        return {
            city: {
                'acquisition_cost': cost,
                'percentage': cost / total * 100 if total > 0 else 0,
            }
            for city, cost in by_city.items()
        }
    
    def update_values(
        self, city_moms: Dict[str, float], observation_id: str = None
    ) -> Dict:
        """Record city MoM indices once, without changing property values."""
        if not observation_id:
            raise ValueError("observation_id is required for an idempotent update")
        results = []
        for p in self.properties:
            if p.city in city_moms:
                results.append(p.update_value(city_moms[p.city], observation_id))
        return {
            'status': INSUFFICIENT_PROPERTY_EVIDENCE,
            'actionable': False,
            'non_actionable': True,
            'property_values_changed': 0,
            'market_context_recorded': sum(
                int(result['market_context_recorded']) for result in results
            ),
            'duplicate_observations': sum(
                int(result['duplicate_observation']) for result in results
            ),
            'observation_conflicts': sum(
                int(result['observation_conflict']) for result in results
            ),
            'observation_id': observation_id,
            'warning': MARKET_CONTEXT_WARNING,
            'properties': results,
        }
    
    def summary(self) -> str:
        """Quarantine legacy personal state that has no identity provenance."""
        return "\n".join(
            [
                "> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | "
                "`actionable: false`  ",
                "> 本文件来自已退役的原 HouseAlice 原型，不属于 DwellProof。内容未经标的、产权、"
                "税费、贷款及成交证据核验，不得用于买卖、估值、预测、排名或风险判断。"
                "DwellProof 入口：`../web/`.\n",
                "# Retired prototype personal-state quarantine\n",
                "> `PERSONAL_STATE_UNVERIFIED` | `actionable: false`",
                "> Legacy account records lack verified identity, source, and "
                "authenticity metadata.",
                "\nProperty count, addresses, costs, values, rent, returns, city "
                "context, and watchlist notes are intentionally not displayed.",
            ]
        )
    
    def save(self, path: str = None):
        """保存到文件"""
        if path is None:
            path = OUTPUT / "uha_data.json"
        path = Path(path)
        data = {
            'name': self.name,
            'properties': [p.to_dict() for p in self.properties],
            'watchlist': self.watchlist,
            'transactions': self.transactions,
            'created_at': self.created_at,
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"UHA 已保存: {path}")
    
    @classmethod
    def load(cls, path: str = None) -> 'UnifiedHousingAccount':
        """从文件加载"""
        if path is None:
            path = OUTPUT / "uha_data.json"
        path = Path(path)
        if not path.exists():
            return cls()
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        uha = cls(name=data.get('name', '我的房产组合'))
        for pd in data.get('properties', []):
            p = Property(**{k: v for k, v in pd.items() if k in [
                'city', 'district', 'address', 'buy_price', 'buy_date',
                'area', 'property_type', 'floor', 'orientation', 'decoration'
            ]})
            saved_value = pd.get('legacy_unverified_value')
            if saved_value is None:
                saved_value = pd.get('current_value')
            p.legacy_unverified_value = saved_value
            p.current_value = None
            p.value_status = INSUFFICIENT_PROPERTY_EVIDENCE
            p.value_observation = pd.get('value_observation')
            saved_context = pd.get('market_context', {})
            if isinstance(saved_context, dict):
                p.market_context = saved_context
            if p.value_observation and p.value_observation not in p.market_context:
                p.market_context[p.value_observation] = {
                    'observation_id': p.value_observation,
                    'city': p.city,
                    'metric': '旧版城市价格指数观测（数值未保留）',
                    'index_value': None,
                    'unit': '未知',
                    'role': 'market_context',
                    'actionable': False,
                    'warning': MARKET_CONTEXT_WARNING,
                }
            saved_rent = pd.get('legacy_unverified_annual_rent')
            if saved_rent is None:
                saved_rent = pd.get('annual_rent')
            p.legacy_unverified_annual_rent = saved_rent
            p.annual_rent = None
            p.notes = pd.get('notes', [])
            uha.properties.append(p)
        uha.watchlist = data.get('watchlist', [])
        uha.transactions = data.get('transactions', [])
        return uha


def demo():
    """Refuse the historical demo so it cannot overwrite a real local account."""
    raise SystemExit(
        "DISABLED_LEGACY_UHA_DEMO: synthetic properties must not be written "
        "to the default personal account path"
    )


if __name__ == "__main__":
    demo()
