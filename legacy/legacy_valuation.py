#!/usr/bin/env python3
"""Retired prototype property-valuation compatibility entry point.

The former city base-price and feature-factor model was not supported by
traceable property-level comparable transactions. It is intentionally
disabled so callers cannot mistake a heuristic number for a valuation.
"""

from datetime import datetime
from pathlib import Path

OUTPUT = Path(__file__).resolve().parent
INSUFFICIENT_PROPERTY_EVIDENCE = "INSUFFICIENT_PROPERTY_EVIDENCE"
VALUATION_WARNING = (
    "旧版静态系数估值已停用；缺少可追溯的房源级可比成交，不能计算单价或总价"
)


class PropertyValuator:
    """Fail-closed compatibility interface for the retired valuation model."""

    def estimate(
        self,
        city,
        district,
        area,
        floor=10,
        orientation='南',
        decoration='精装',
    ):
        """Refuse valuation until verified property-level evidence is supplied.

        This legacy API has no fields for comparable transaction identity,
        source, transaction date, property match, or verification state. It
        therefore cannot safely produce a price even for a known city/district.
        """
        if isinstance(area, bool) or not isinstance(area, (int, float)) or area <= 0:
            raise ValueError("area must be a positive number")

        return {
            'city': city,
            'district': district,
            'area': area,
            'floor': floor,
            'orientation': orientation,
            'decoration': decoration,
            'status': INSUFFICIENT_PROPERTY_EVIDENCE,
            'actionable': False,
            'non_actionable': True,
            'valuation_available': False,
            'missing_evidence': [
                '可追溯的房源级可比成交',
                '可比成交日期与来源',
                '标的与可比案例的关键属性匹配',
                '可复核的估值调整依据',
            ],
            'error': VALUATION_WARNING,
            'warning': VALUATION_WARNING,
        }

    def batch_estimate(self, properties):
        """Return an individual refusal record for every requested property."""
        return [self.estimate(**prop) for prop in properties]


def render_refusal_report(results):
    """Render refusal records without valuation fields or price columns."""
    lines = [
        "> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | "
        "`actionable: false`  ",
        "> 本文件来自已退役的原 HouseAlice 原型，不属于 DwellProof。内容未经标的、产权、"
        "税费、贷款及成交证据核验，不得用于买卖、估值、预测、排名或风险判断。"
        "DwellProof 入口：`../web/`.\n",
        "# 退役原型房产估值报告（旧版拒答）\n",
        f"> {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"> **状态: `{INSUFFICIENT_PROPERTY_EVIDENCE}`（不可操作）**  ",
        f"> {VALUATION_WARNING}。",
        "\n## 请求记录\n",
        "| 城市 | 区域 | 面积 | 估值状态 | 结果 |",
        "|------|------|------|----------|------|",
    ]
    for result in results:
        lines.append(
            f"| {result['city']} | {result['district']} | "
            f"{result['area']}㎡ | `{result['status']}` | 未计算 |"
        )
    return "\n".join(lines)


def demo():
    """Generate a refusal report without displaying pseudo-precise prices."""
    print("=" * 60)
    print("  退役原型 — 房产估值模型（旧版已停用）")
    print("=" * 60)

    properties = [
        {'city': '广州', 'district': '天河', 'area': 89, 'floor': 25,
         'orientation': '南', 'decoration': '精装'},
        {'city': '上海', 'district': '浦东内环', 'area': 120, 'floor': 30,
         'orientation': '东南', 'decoration': '豪装'},
        {'city': '北京', 'district': '海淀', 'area': 80, 'floor': 15,
         'orientation': '南', 'decoration': '精装'},
        {'city': '深圳', 'district': '南山', 'area': 90, 'floor': 20,
         'orientation': '南', 'decoration': '精装'},
        {'city': '成都', 'district': '高新', 'area': 100, 'floor': 12,
         'orientation': '南', 'decoration': '精装'},
    ]
    results = PropertyValuator().batch_estimate(properties)
    report = render_refusal_report(results)
    print(report)
    report_path = OUTPUT / "VALUATION_REPORT.md"
    with report_path.open("w", encoding="utf-8") as handle:
        handle.write(report)
    print(f"\n报告已保存: {report_path}")


if __name__ == "__main__":
    demo()
