#!/usr/bin/env python3
"""Retired legacy calculator entry point.

The former script embedded example mortgage rates, down-payment ratios, seller
taxes, agent fees and an incorrect early-repayment calculation. Those values
depend on a dated bank quote, transaction location, parties and contract, so the
legacy batch report now fails closed instead of regenerating misleading tables.
"""

from pathlib import Path


OUTPUT = Path(__file__).resolve().parent
STATUS = "INSUFFICIENT_EVIDENCE"


def build_refusal_report() -> str:
    return "\n".join(
        [
            "> **LEGACY_ARCHIVE_UNVERIFIED** | `INSUFFICIENT_EVIDENCE` | `actionable: false`  ",
            "> 本文件来自已退役的原 HouseAlice 原型，不属于 DwellProof。内容未经标的、产权、"
            "税费、贷款及成交证据核验，不得用于买卖、估值、预测、排名或风险判断。"
            "DwellProof 入口：`../web/`。",
            "",
            "# 原型旧计算器已停用",
            "",
            f"> 状态: `{STATUS}`（不可操作）",
            "",
            "旧脚本中的固定贷款利率、首付比例、卖方税费、中介费、租售比判断和提前还贷结果均未绑定可追溯的标的级证据，现已停止生成。",
            "",
            "请使用根目录 `core/` 中的版本化计算模块，并提供：",
            "",
            "- 带日期和来源的银行书面执行利率；",
            "- 当地官方税费规则、计税基础和交易双方承担方式；",
            "- 标的成交价、租金、空置、持有和退出成本证据；",
            "- 实际贷款余额、剩余期限、还款方式和提前还款条款。",
            "",
            "在这些证据补齐前，不计算月供、税费、利润、收益率或提前还贷节省额。",
        ]
    )


def main() -> int:
    report = build_refusal_report()
    target = OUTPUT / "CALCULATOR_TOOLS.md"
    target.write_text(report + "\n", encoding="utf-8")
    print(report)
    print(f"\n拒答报告已保存: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
