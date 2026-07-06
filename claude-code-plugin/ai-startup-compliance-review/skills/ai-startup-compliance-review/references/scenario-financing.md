# Scenario: Financing Diligence

Use this file for fundraising, investor due diligence, disclosure schedules, and valuation-sensitive compliance review.

## Review Focus

- Whether core data, model, code, and IP assets are lawfully controlled by the company.
- Whether investor-facing AI, data, privacy, security, and IP claims are substantiated.
- Whether unresolved compliance issues require disclosure, conditions precedent, escrow, indemnity, or valuation adjustment.

## Intake Checklist

- Financing stage and investor diligence scope.
- Core model ownership and whether any third-party API/model is essential.
- Training/fine-tuning data sources, licenses, scraping, customer data, and public data.
- Employee/contractor invention assignments.
- Open-source software, open-weight models, and license restrictions.
- Privacy/data security incidents, complaints, investigations, and pending disputes.
- Prior marketing or pitch claims about AI accuracy, bias, privacy, security, or proprietary data.

## Typical Risks

| Risk | Default domain | Notes |
|---|---|---|
| Core model not fully owned | IP | L3/L4 if asset is material to valuation |
| Training data provenance unclear | Data/IP/AI | Escalate if scraped, personal, confidential, or copyrighted |
| Open-source/model license conflict | IP | Review copyleft, commercial limits, attribution, model-use restrictions |
| AI capability exaggeration | Consumer/marketing | Investor statements can create securities or misrepresentation exposure |
| Undisclosed data incident or regulator contact | Data/cybersecurity | Usually L3+ until assessed |
| Missing compliance controls for regulated launch | AI/data | May become condition precedent |

## Output Additions

Add a financing-specific section:

```markdown
## 融资尽调披露建议
| 披露事项 | 重要性 | 投资人可能关注点 | 建议披露/整改口径 |
```

Use "condition to closing" language when a gap affects core asset ownership, legality of data assets, or investor representations.
