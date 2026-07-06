# Intake Router

Use this file to map the user's request to scenario and domain references.

## Primary Scenario Signals

| Scenario | User signals | Required scenario file |
|---|---|---|
| Financing diligence | fundraising, investor DDQ, due diligence, disclosure, valuation, "数据资产", "模型所有权" | `scenario-financing.md` |
| Data processing | training data, scraping, annotation, fine-tuning, PI, sensitive PI, minors, retention, sharing | `scenario-data-processing.md` |
| Product launch | launch, release, feature review, app上线, chatbot, recommender, customer-facing AI | `scenario-product-launch.md` |
| Cross-border | overseas users, data export, foreign market, EU/US, export control, sanctions, global deployment | `scenario-cross-border.md` |
| Vendor contract | model API, SaaS, supplier, procurement, DPA, terms, training on prompts, subprocessor | `scenario-vendor-contract.md` |

## Domain Trigger Signals

Load domain files only when facts trigger them:

- AI governance: model behavior, generated content, automated decisions, safety testing, human oversight, bias, hallucination.
- Data compliance: personal information, sensitive personal information, minors, important data, data export, consent, privacy notice.
- IP: training data rights, output ownership, open-source models/code, contractor ownership, trade secrets.
- Cybersecurity: authentication, access control, API abuse, logs, leakage, incident response, vulnerability exposure.
- Consumer and marketing: user-facing claims, pricing, recommendations, advertisements, minors, vulnerable users.

## Routing Rules

- Select one dominant scenario first.
- Add secondary scenarios only when they change the review path.
- When facts are insufficient, ask targeted intake questions instead of loading every scenario.
- For urgent launch or investment requests, proceed with explicit assumptions and list missing evidence.
