# Scenario: Cross-Border

Use this file for overseas launch, foreign users, global model deployment, cross-border data transfers, export control, sanctions, and platform-policy issues.

## Review Focus

- Target markets and affected persons.
- Data transfer path, hosting location, vendor location, and remote access.
- Role split: provider, deployer, controller, processor, customer, reseller.
- Conflicts between China-focused controls and foreign regulatory expectations.
- Geopolitical, export-control, sanctions, and platform-policy exposure where relevant.

## Intake Checklist

- Target jurisdictions and launch timeline.
- User categories and data subjects.
- Data categories and whether personal information, sensitive data, or important data crosses borders.
- Hosting, support, analytics, model API, and subcontractor locations.
- Whether the company provides AI system, deploys AI system, or resells/integrates third-party AI.
- Industry: finance, health, education, employment, public sector, critical infrastructure, children.
- Export-control, sanctions, restricted-party, and app-store/platform constraints.

## Typical Risks

| Risk | Level guide |
|---|---|
| Cross-border personal information transfer with no assessment/mechanism | L3/L4 |
| Important data or sensitive data export uncertainty | L3/L4 |
| High-impact AI in foreign market with no local role analysis | L3 |
| Vendor stack makes data residency promises impossible | L3 |
| Sanctions/export-control screening missing for restricted markets | L3/L4 |
| Inconsistent privacy notices across jurisdictions | L2/L3 |

## Review Path

- Map data flows by country and vendor.
- Identify strictest applicable transfer/control requirements.
- Decide localization, transfer mechanism, or market deferral.
- Review foreign-facing notices, user rights, complaint channels, and AI disclosures.
- Screen vendors, customers, and markets when sanctions/export-control risk is plausible.

## Output Additions

Add:

```markdown
## 出海/跨境专项判断
| 市场 | 角色 | 数据路径 | 主要风险 | 建议 |
```
