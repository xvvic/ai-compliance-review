#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
detect_risks.py —— 风险规则库确定性预扫描
============================================
读取企业材料(txt/md/docx/pdf)与 risk_rules.yaml, 输出命中的风险规则清单(JSON)。
用途:
  - Agent 在风险分类前运行本脚本, 把命中结果作为风险触发核对清单
  - E2/评测流程复用本脚本的结构化输出

用法:
    python detect_risks.py 待审查材料.txt
    python detect_risks.py 样例.docx --rules /path/to/risk_rules.yaml
    python detect_risks.py 样例.pdf   # 输出 JSON 到 stdout

说明:
  - 关键词命中为确定性匹配(大小写不敏感, 计出现次数);
  - trigger.semantic 供 LLM 语义判断用, 本脚本原样带出不参与匹配;
  - 一票升级: escalation.condition_keywords 任一命中即取最高等级;
  - L3 及以上或规则声明 human_review 的条目要求人工复核。
"""

import json
import re
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
# 插件布局: <plugin_root>/skills/ai-startup-compliance-review/scripts/ -> 规则库在插件根
_RULE_CANDIDATES = [
    SCRIPT_DIR.parent.parent.parent / "risk_rules.yaml",  # 标准插件布局
    SCRIPT_DIR.parent / "risk_rules.yaml",                 # skill 根旁
    Path.cwd() / "risk_rules.yaml",                        # 当前目录兜底
]
DEFAULT_RULES = next((p for p in _RULE_CANDIDATES if p.exists()), _RULE_CANDIDATES[0])

LEVEL_ORDER = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}


def read_material(path: str) -> str:
    p = Path(path)
    suffix = p.suffix.lower()
    if suffix in (".txt", ".md"):
        return p.read_text(encoding="utf-8", errors="ignore")
    if suffix == ".docx":
        import docx

        doc = docx.Document(str(p))
        return "\n".join(par.text for par in doc.paragraphs)
    if suffix == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(str(p))
        return "\n".join((page.extract_text() or "") for page in reader.pages)
    raise ValueError(f"不支持的文件类型: {suffix}(支持 txt/md/docx/pdf)")


def count_hits(text: str, keywords: list) -> dict:
    """返回 {关键词: 出现次数}, 大小写不敏感。"""
    hits = {}
    lowered = text.lower()
    for kw in keywords or []:
        kw_l = str(kw).lower()
        if not kw_l:
            continue
        n = lowered.count(kw_l)
        if n:
            hits[str(kw)] = n
    return hits


def detect(text: str, rules_doc: dict) -> dict:
    """对整份材料跑全部规则, 返回结构化命中结果。"""
    # 企业画像提示
    profile = {}
    for label, kws in (rules_doc.get("profile_keywords", {}).get("product_type") or {}).items():
        hits = count_hits(text, kws)
        if hits:
            profile[label] = hits
    third_party = count_hits(text, rules_doc.get("profile_keywords", {}).get("third_party_model") or [])
    if third_party:
        profile["第三方模型依赖"] = third_party

    matched = []
    for rule in rules_doc.get("rules", []):
        kw_hits = count_hits(text, rule.get("trigger", {}).get("keywords") or [])
        if not kw_hits:
            continue
        level = rule.get("default_level", "L2")
        escalated, escalation_hits = False, []
        for esc in rule.get("escalation") or []:
            esc_hits = count_hits(text, esc.get("condition_keywords") or [])
            if esc_hits:
                escalated = True
                escalation_hits.append(
                    {
                        "reason": esc.get("reason", ""),
                        "level": esc.get("level"),
                        "matched_keywords": esc_hits,
                    }
                )
                if LEVEL_ORDER.get(esc.get("level"), 0) > LEVEL_ORDER.get(level, 0):
                    level = esc["level"]
        human_review = rule.get("human_review", False) or LEVEL_ORDER.get(level, 0) >= 3
        matched.append(
            {
                "id": rule.get("id"),
                "category": rule.get("category"),
                "risk_type": rule.get("risk_type"),
                "matched_keywords": kw_hits,
                "default_level": rule.get("default_level"),
                "final_level": level,
                "escalated": escalated,
                "escalation_detail": escalation_hits,
                "human_review_required": human_review,
                "semantic_cues": rule.get("trigger", {}).get("semantic") or [],
                "evidence_needed": rule.get("evidence_needed") or [],
                "remediation_hint": rule.get("remediation_hint", ""),
                "refs": rule.get("refs") or {},
            }
        )

    matched.sort(key=lambda r: (-LEVEL_ORDER.get(r["final_level"], 0), r["id"]))
    by_level = {}
    for r in matched:
        by_level[r["final_level"]] = by_level.get(r["final_level"], 0) + 1
    return {
        "profile_hints": profile,
        "matched_rules": matched,
        "summary": {
            "total_matched": len(matched),
            "by_level": by_level,
            "human_review_required": sum(1 for r in matched if r["human_review_required"]),
        },
    }


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    material = args[0]
    rules_path = DEFAULT_RULES
    if "--rules" in args:
        rules_path = Path(args[args.index("--rules") + 1])

    rules_doc = yaml.safe_load(rules_path.read_text(encoding="utf-8"))
    text = read_material(material)
    if not text.strip():
        print(json.dumps({"error": "材料解析为空"}, ensure_ascii=False))
        sys.exit(1)

    result = detect(text, rules_doc)
    result["material"] = Path(material).name
    result["rules_file"] = str(rules_path)
    result["material_chars"] = len(text)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
