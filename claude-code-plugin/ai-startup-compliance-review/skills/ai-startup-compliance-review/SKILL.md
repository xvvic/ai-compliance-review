---
name: ai-startup-compliance-review
description: This skill should be used when the user asks for AI startup compliance review, AI product launch review, training data compliance, algorithm or generative AI risk assessment, AI cross-border expansion review, AI vendor or model contract review, science-and-technology enterprise risk identification, financing diligence involving data/IP/model compliance, or Chinese AI company compliance workflow reports.
---

# AI Startup Compliance Review

## Purpose

Review AI startup business scenarios for compliance risk, evidence gaps, and practical remediation. Produce structured work product: scenario profile, risk matrix, review path, source appendix, and acceptance criteria.

Keep this folder self-contained. When installed as a Claude Code plugin, treat `${CLAUDE_PLUGIN_ROOT}/legal_preference_txt` as the packaged local corpus root and `${CLAUDE_PLUGIN_ROOT}/skills/ai-startup-compliance-review/scripts/` as the helper script location.

## Hard Rules

- Use local corpus material under `${CLAUDE_PLUGIN_ROOT}/legal_preference_txt` first when the plugin is installed, or `legal_preference_txt/` when the skill is used standalone.
- Use 北大法宝 MCP as an approved retrieval dependency when it is configured and local sources are insufficient or need cross-checking.
- Do not describe 北大法宝 MCP results as final legal verification or write claims such as "北大法宝已核验" or "经北大法宝检索即可视为最终结论".
- Tag every legal, regulatory, case, policy, or source-backed claim with the source class defined in `references/00-source-policy.md`.
- Mark model-only legal reasoning as `[模型推理-待核验]`.
- Do not present the output as a final legal opinion. Frame it as compliance review work product requiring human verification.
- Keep context lean: load only the scenario, stage, and domain references needed for the matter.

## Core Workflow

1. Read `references/00-source-policy.md`, `references/01-intake-router.md`, and `references/02-risk-scoring.md`.
2. Classify the user's request into one dominant scenario and any secondary scenarios.
3. Load the dominant scenario reference. Load secondary scenario references only when facts require cross-checks.
4. Load stage references as needed:
   - `references/stage-intake.md` for missing facts and interview questions.
   - `references/stage-retrieval.md` before searching or citing local corpus material.
   - `references/stage-risk-classification.md` before assigning risk levels.
   - `references/stage-remediation.md` before drafting corrective actions.
5. Load only domain references triggered by the facts.
6. Search local sources first when legal authority, enforcement examples, or risk-framework support is needed. If configured, use 北大法宝 MCP as the next retrieval layer for regulations, cases, exact article lookup, and citation checking.
7. Produce the report using `references/03-output-template.md`.
8. Run `${CLAUDE_PLUGIN_ROOT}/skills/ai-startup-compliance-review/scripts/check_report_structure.py` on saved report drafts when the plugin is installed, or `scripts/check_report_structure.py` when the skill is used standalone.

## Retrieval Order

1. Search `${CLAUDE_PLUGIN_ROOT}/legal_preference_txt` first when running inside the plugin, or `legal_preference_txt/` when using the skill standalone.
2. If local support is thin, stale, or missing a specific regulation/case, use 北大法宝 MCP if available.
3. Before citing a concrete article number in a final report, prefer exact article lookup and citation validation when those MCP tools are available.
4. If both local retrieval and MCP retrieval fail, write `[待核验: 缺少来源支持]` and continue with explicit uncertainty.

## Scenario Routing

| User matter | Load this scenario reference |
|---|---|
| Financing, diligence, fundraising, investor questionnaire, disclosure schedule | `references/scenario-financing.md` |
| Training data, fine-tuning, data collection, PII processing, data sharing, retention | `references/scenario-data-processing.md` |
| Product launch, feature review, go/no-go review, release risk | `references/scenario-product-launch.md` |
| Overseas launch, data export, foreign users, global deployment, sanctions/export-control issues | `references/scenario-cross-border.md` |
| AI vendor, model API, SaaS contract, DPA, model terms, procurement | `references/scenario-vendor-contract.md` |

If the scenario is unclear, read `references/stage-intake.md`, ask no more than five targeted questions, then proceed with explicit assumptions if the user wants a fast first pass.

## Domain Routing

| Trigger facts | Load this domain reference |
|---|---|
| AI model, generative AI, algorithmic decisioning, human oversight, bias, hallucination, safety testing | `references/domain-ai-governance.md` |
| Personal information, sensitive PI, minors, important data, data export, privacy notice, consent, PIA/DPIA | `references/domain-data-compliance.md` |
| Training data copyright, generated outputs, model ownership, open-source software/model, employee invention, trade secret | `references/domain-ip.md` |
| API security, access control, logs, prompt/document leakage, model abuse, incident response | `references/domain-cybersecurity.md` |
| Marketing claims, consumer disclosure, algorithmic pricing/recommendation, minors, vulnerable users | `references/domain-consumer-marketing.md` |

## Output Discipline

- Give a one-page conclusion first when producing a report.
- Tie each L3/L4 risk to a concrete triggering fact, source or verification gap, and remediation action.
- Separate known facts, assumptions, retrieved sources, and model reasoning.
- Make the overall recommendation match the highest unresolved risk:
  - L1: proceed with records.
  - L2: proceed with conditions.
  - L3: pause or escalate before launch/closing.
  - L4: do not proceed until redesigned or externally verified.
- Include a "待核验清单" for missing facts, outdated law risk, source uncertainty, and human counsel review.

## Scripts

- `scripts/search_corpus.py`: search local text corpus and emit source-tagged snippets.
- `scripts/score_risk.py`: compute a repeatable risk level from structured factors.
- `scripts/check_report_structure.py`: validate report sections, accepted source tags including 北大法宝 MCP labels, forbidden pseudo-verification claims, and high-risk remediation coverage.
