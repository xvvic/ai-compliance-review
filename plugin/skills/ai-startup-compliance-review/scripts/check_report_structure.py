#!/usr/bin/env python3
"""Validate AI startup compliance review report structure."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = (
    "## 1. 一页结论",
    "## 2. 场景画像",
    "## 3. 风险矩阵",
    "## 4. 审查路径",
    "## 5. 整改清单",
    "## 6. 来源与待核验清单",
    "## 7. 残余风险与复查触发条件",
)

SOURCE_TAGS = (
    "[本地法规库",
    "[本地案例",
    "[本地论文/报告",
    "[北大法宝MCP",
    "[用户材料",
    "[模型推理-待核验",
    "[待核验",
)

FORBIDDEN_PATTERNS = (
    "北大法宝已核验",
    "经北大法宝检索",
    "经北大法宝MCP检索即可视为最终结论",
    "经Pkulaw MCP检索即可视为最终结论",
)


def validate_text(text: str) -> list[str]:
    errors: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"missing section: {section}")

    for pattern in FORBIDDEN_PATTERNS:
        if pattern in text:
            errors.append(f"forbidden source claim: {pattern}")

    if "## 3. 风险矩阵" in text and not any(tag in text for tag in SOURCE_TAGS):
        errors.append("no recognized source or verification tag found")

    high_risk_lines = [
        line for line in text.splitlines()
        if re.search(r"\|\s*L[34]\b|\bL[34]\b", line)
    ]
    remediation_present = "## 5. 整改清单" in text and re.search(r"验收标准|整改|处理建议|放行条件", text) is not None
    if high_risk_lines and not remediation_present:
        errors.append("L3/L4 risk appears without remediation language")

    if "总体风险等级" in text:
        matrix_levels = set(re.findall(r"\bL[1-4]\b", text))
        if matrix_levels and not re.search(r"总体风险等级[：:： ]+\s*L[1-4]", text):
            errors.append("overall risk level field is present but no L1-L4 value was found near it")

    return errors


def run_self_test() -> None:
    valid = """# AI 初创公司合规审查报告

## 1. 一页结论
- 总体风险等级：L3

## 2. 场景画像

## 3. 风险矩阵
| 风险 | 领域 | 等级 | 来源/依据 | 处理建议 |
|---|---|---|---|---|
| 训练数据来源不清 | 数据/IP | L3 | [用户材料: 访谈] | 暂缓上线 |

## 4. 审查路径

## 5. 整改清单
| 整改项 | 验收标准 |
|---|---|
| 建立数据集台账 | 覆盖来源和授权 |

## 6. 来源与待核验清单

## 7. 残余风险与复查触发条件
"""
    invalid = valid.replace("## 4. 审查路径\n", "")
    pkulaw_only = valid.replace("[用户材料: 访谈]", "[北大法宝MCP: pkulaw-law-search/search_article | 生成式人工智能 | 2026-07-05]")
    assert validate_text(valid) == []
    assert any("missing section" in item for item in validate_text(invalid))
    assert validate_text(pkulaw_only) == []
    assert any("forbidden" in item for item in validate_text(valid + "\n北大法宝已核验"))
    assert any("forbidden" in item for item in validate_text(valid + "\n经北大法宝MCP检索即可视为最终结论"))
    print("self-test passed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", nargs="?", help="Markdown report path")
    parser.add_argument("--self-test", action="store_true", help="run built-in tests")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        return 0
    if not args.report:
        parser.error("report path is required unless --self-test is used")

    text = Path(args.report).read_text(encoding="utf-8")
    errors = validate_text(text)
    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        return 1
    print("report structure valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
