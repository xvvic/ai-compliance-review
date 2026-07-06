# Scenario: Vendor Contract

Use this file for AI vendor, model API, SaaS, DPA, procurement, subprocessor, and model terms review.

## Review Focus

- Whether vendor use of prompts, uploads, outputs, logs, and metadata is compatible with company obligations.
- Whether contract rights support confidentiality, privacy, IP ownership, auditability, deletion, and incident response.
- Whether upstream model providers or subprocessors create unallocated risk.

## Intake Checklist

- Vendor service and whether AI/model functionality is core or auxiliary.
- Data submitted: prompts, documents, customer data, personal information, confidential data, source code.
- Whether vendor may train or improve models on submitted data.
- Retention, deletion, data residency, logging, and human review.
- Subprocessors/upstream model providers.
- Output ownership and usage restrictions.
- Security controls, audit reports, incident notice, vulnerability handling.
- Liability cap, indemnity, warranty disclaimers, service changes, termination assistance.

## Clause Review Matrix

| Clause issue | Preferred position |
|---|---|
| Training on customer data | No training or improvement without explicit written opt-in |
| Confidentiality | Prompts, uploads, outputs, logs, and metadata covered |
| Personal information | Processor obligations, documented instructions, deletion, subprocessors |
| Data residency | Clear storage/processing locations or approved exception |
| Incident notice | Prompt notice with facts, containment, and cooperation |
| Model changes | Notice for material changes affecting risk, output quality, or compliance |
| Output/IP | Customer can use outputs; vendor does not claim customer inputs or confidential derivatives |
| Auditability | Security reports, questionnaires, audit rights, or equivalent evidence |
| Liability | Caps and exclusions aligned with data, confidentiality, IP, and security exposure |

## Red Flags

- Vendor may train on confidential, personal, or customer data by default.
- Vendor can retain prompts/uploads indefinitely.
- No subprocessor transparency.
- Output ownership or use restrictions conflict with product promises.
- Liability cap excludes the main foreseeable harm.
- Vendor can materially change model behavior with no notice.
