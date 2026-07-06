# Scenario: Data Processing

Use this file for training data, fine-tuning, scraping, personal information processing, data sharing, and retention reviews.

## Review Focus

- Data lifecycle: collection, source, lawful basis, notice, consent, use, sharing, export, retention, deletion.
- Special categories: sensitive personal information, minors, biometric data, health, finance, location, identity, confidential documents, important data.
- AI-specific use: model training, fine-tuning, evaluation, prompt logging, retrieval augmentation, human annotation, and synthetic data generation.

## Intake Checklist

- Data categories and volume.
- Source: user submitted, customer records, public web, purchased dataset, partner, vendor, employee, synthetic.
- Whether data includes personal information, sensitive personal information, minors, confidential information, trade secrets, or important data.
- Purpose and whether the purpose differs from original collection.
- Notice/consent or other lawful basis.
- Data processors/vendors and cross-border transfers.
- Retention, deletion, access control, audit logs, and incident process.

## Typical Risks

| Risk | Level guide |
|---|---|
| No lawful basis for personal information processing | L3/L4 |
| Sensitive PI/minors data without enhanced controls | L3/L4 |
| Public web scraping used as unrestricted training data | L2-L4 depending on content and controls |
| Customer confidential documents retained for training | L3/L4 |
| Data sharing with vendor not covered by contract | L2/L3 |
| Missing PIA/DPIA-style assessment for high-risk processing | L2/L3 |
| Data export path not assessed | L3/L4 |

## Review Path

- Create data inventory and data-flow map.
- Classify data categories and affected subjects.
- Confirm lawful basis and notice/consent.
- Assess necessity and minimization.
- Review processor/vendor contracts.
- Assess export triggers.
- Define retention, deletion, access, and incident controls.

## Required Artifacts

- Dataset register.
- Data-flow diagram or table.
- PIA/DPIA-style assessment.
- Vendor/processor list.
- User notice and consent evidence.
- Deletion and retention policy.
