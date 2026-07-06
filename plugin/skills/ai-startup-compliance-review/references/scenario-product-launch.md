# Scenario: Product Launch

Use this file for launch reviews, feature releases, go/no-go decisions, and customer-facing AI functionality.

## Review Focus

- Whether the feature changes data collection, AI output risk, user reliance, consumer disclosure, or cybersecurity exposure.
- Whether launch should be clear, conditional, escalated, or blocked.

## Intake Checklist

- Feature description, launch date, user group, and rollback path.
- AI component: model type, provider, fine-tuning, RAG, automated decisioning, human review.
- Data collected, logged, retained, shared, or exported.
- Output type: advice, ranking, pricing, eligibility, moderation, diagnosis, legal/financial content, generated media.
- User disclosures, complaint path, appeal path, and human override.
- Safety testing: hallucination, bias, jailbreak, toxicity, privacy leakage, security abuse.
- Marketing claims and public statements.

## Launch Decision Categories

| Decision | Meaning |
|---|---|
| Clear | L1 only; normal records and monitoring are enough |
| Conditional | L2 risks; launch after listed controls are complete |
| Escalate | L3 risks; legal/security/product owner review before launch |
| Block | L4 risks; redesign or external verification required |

## Common High-Risk Launch Triggers

- AI output affects rights, access, employment, finance, health, education, or public services.
- Product serves minors or vulnerable users.
- Generated content may impersonate, defame, mislead, or violate rights.
- Personal or confidential data is logged into third-party model services.
- User-facing claims promise accuracy, no bias, privacy, or security without evidence.
- No incident response, logging, rollback, or complaint path exists.

## Output Additions

Add:

```markdown
## 上线门禁
| 门禁项 | 状态 | 未完成风险 | 放行条件 |
```

Use "附条件上线" only when every condition has an owner and acceptance criterion.
