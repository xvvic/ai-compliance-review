# Stage: Risk Classification

Use this file after intake and retrieval, before final report drafting.

## Classification Steps

1. List each risk as a separate row. Avoid combining unrelated legal, technical, and business risks.
2. Identify triggering facts from user materials or assumptions.
3. Identify source support or source gap.
4. Apply `02-risk-scoring.md` factors.
5. Check red-line triggers.
6. Assign level and confidence.
7. Verify that the overall recommendation matches the highest unresolved risk.

## Required Fields Per Risk

- Risk title.
- Domain.
- Level: L1, L2, L3, or L4.
- Confidence: High, Medium, or Low.
- Triggering fact.
- Source or verification gap.
- Remediation action.

## Escalation Rules

- Escalate to L3 when facts suggest regulated AI, large-scale personal information, sensitive data, minors, material IP ambiguity, or unsubstantiated high-stakes claims.
- Escalate to L4 when no lawful basis, no source support, or no practical mitigation exists for a core product or transaction dependency.
- Do not downgrade risk because the company is early-stage. Early-stage status affects remediation path, not legal exposure.

## Common Misclassification Errors

- Treating privacy notice updates as enough when data use has no lawful basis.
- Treating vendor assurances as enough without contract rights, auditability, deletion, and incident notice.
- Treating "public web data" as automatically usable for model training.
- Treating generated output ownership as settled without reviewing model/vendor terms.
- Treating marketing AI claims as harmless when investors or consumers may rely on them.
