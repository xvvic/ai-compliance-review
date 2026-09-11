# -*- coding: utf-8 -*-
"""规则层预扫描与报告风险条目的合并。

合并策略:
- 报告条目按 rule_id 挂到对应预扫描规则上(等级取报告值,但规则层的一票升级/
  L3+ 复核要求保留,防止模型降级绕过人工复核);
- 报告中 rule_id 为空的新发现风险,编号 SEM-001 起独立成条;
- 预扫描命中但报告未提及的规则保留(in_report=False),作为确定性底线。
"""

LEVEL_ORDER = {"L1": 1, "L2": 2, "L3": 3, "L4": 4}


def _level(value):
    return value if value in LEVEL_ORDER else None


def merge_risk_items(matched_rules, report_risks):
    """matched_rules: detect() 输出的规则命中;report_risks: 风险条目.json 的 risks 列表。"""
    matched_rules = matched_rules or []
    report_risks = report_risks or []
    by_rule = {}
    semantic = []
    for item in report_risks:
        if not isinstance(item, dict):
            continue
        rid = item.get("rule_id")
        if rid and rid in {r.get("id") for r in matched_rules}:
            by_rule[rid] = item
        else:
            semantic.append(item)

    merged = []
    for rule in matched_rules:
        rid = rule.get("id")
        report_item = by_rule.get(rid)
        rule_level = rule.get("final_level")
        report_level = _level(report_item.get("level")) if report_item else None
        final_level = report_level or rule_level or "L2"
        must_review = bool(rule.get("human_review_required")) or LEVEL_ORDER.get(final_level, 0) >= 3 \
            or LEVEL_ORDER.get(rule_level, 0) >= 3
        merged.append({
            **rule,
            "source": "rule+report" if report_item else "rule",
            "in_report": report_item is not None,
            "rule_level": rule_level,
            "report_level": report_level,
            "final_level": final_level,
            "human_review_required": must_review,
            "trigger_fact": (report_item or {}).get("trigger_fact", ""),
            "report_evidence": (report_item or {}).get("evidence", ""),
            "recommendation": (report_item or {}).get("recommendation", "") or rule.get("remediation_hint", ""),
        })

    for i, item in enumerate(semantic, 1):
        level = _level(item.get("level")) or "L2"
        merged.append({
            "id": "SEM-%03d" % i,
            "source": "semantic",
            "in_report": True,
            "category": item.get("category") or "语义识别",
            "risk_type": item.get("risk") or "语义识别风险",
            "matched_keywords": {},
            "default_level": level,
            "rule_level": None,
            "report_level": level,
            "final_level": level,
            "escalated": False,
            "escalation_detail": [],
            "human_review_required": LEVEL_ORDER.get(level, 0) >= 3,
            "semantic_cues": [],
            "evidence_needed": [],
            "remediation_hint": item.get("recommendation", ""),
            "trigger_fact": item.get("trigger_fact", ""),
            "report_evidence": item.get("evidence", ""),
            "recommendation": item.get("recommendation", ""),
            "confidence": item.get("confidence", ""),
            "refs": {},
        })

    merged.sort(key=lambda r: (-LEVEL_ORDER.get(r.get("final_level"), 0), str(r.get("id"))))
    return merged
