# Risk Scoring

Use this file before assigning Low/Medium/High/Stop conclusions.

## Levels

| Level | Meaning | Action |
|---|---|---|
| L1 Low | Routine compliance record issue or low exposure | Proceed with records and monitoring |
| L2 Medium | Real gap exists but can be controlled with conditions | Proceed only after specified controls |
| L3 High | Material legal, regulatory, technical, ethics, or business exposure | Pause or escalate before launch, closing, or signing |
| L4 Stop / Red Line | Likely prohibited, unverifiable, structurally unsafe, or cannot be remediated in current design | Do not proceed until redesigned or externally verified |

## Factor Scores

Score each factor 0-3:

| Factor | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Legal trigger | none | uncertain | likely applies | clear trigger or formal obligation |
| Severity | negligible | manageable | material | severe, systemic, or enforcement-prone |
| Likelihood | remote | possible | likely | active or imminent |
| Controllability | strong controls | partial controls | weak controls | no viable controls |
| Affected population | internal only | small group | broad users | minors, vulnerable users, or public-scale impact |
| Source confidence | strong sources | adequate sources | weak sources | no source for key claim |

## Mapping

- 0-4: L1
- 5-8: L2
- 9-13: L3
- 14-18: L4

Override upward when a red line applies.

## Red-Line Triggers

Classify as L4 unless facts prove otherwise:

- Sensitive personal information, minors' data, biometric data, or large-scale scraping with no lawful basis.
- Production launch of high-impact AI without human oversight, logging, complaint path, or safety testing.
- Data export involving personal information or important data with no transfer mechanism assessment.
- Vendor terms allowing unrestricted training on confidential or personal data.
- Marketing or investor claims about AI capability, bias, accuracy, privacy, or security that cannot be substantiated.
- Material IP ownership gap over core model, training data, or key code assets before financing.

## Confidence

Add confidence to each risk conclusion:

- High: key facts and source support are present.
- Medium: key facts are present but sources or controls need review.
- Low: conclusion depends on assumptions, missing documents, or model-only reasoning.
