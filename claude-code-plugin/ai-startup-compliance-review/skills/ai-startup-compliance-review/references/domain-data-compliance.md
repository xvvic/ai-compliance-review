# Domain: Data Compliance

Use this file for personal information, sensitive personal information, minors, important data, data export, privacy notices, consent, and PIA/DPIA-style review.

## Data Categories

- Personal information: information related to identified or identifiable natural persons.
- Sensitive personal information: data that can easily cause dignity harm or personal/property safety harm if leaked or misused; examples often include biometrics, religious belief, specific identity, medical health, finance, location tracks, and minors' personal information.
- Important data: data that may affect national security, economic operation, social stability, public health, or safety if tampered with, destroyed, leaked, illegally obtained, or illegally used.
- Confidential business data: customer documents, trade secrets, source code, contracts, internal policies, and non-public operational data.

## Lifecycle Review

1. Collection source and lawful basis.
2. Notice, consent, or other authorization.
3. Purpose limitation and compatibility with original purpose.
4. Necessity and minimization.
5. Storage, access control, retention, and deletion.
6. Sharing, entrusted processing, and joint processing.
7. Cross-border transfer.
8. User rights, complaints, and incident response.

## AI-Specific Data Issues

- Training/fine-tuning may be a new processing purpose.
- Prompt logs and uploaded files can contain personal or confidential data.
- RAG corpora can leak source documents through generated outputs.
- Synthetic data can still be personal data if re-identification risk remains.
- Publicly accessible data is not automatically free of privacy, copyright, or contract limits.

## Required Artifacts

- Data inventory.
- Data-flow map.
- Privacy notice and consent evidence.
- PIA/DPIA-style assessment for high-risk processing.
- Vendor processor agreements.
- Retention/deletion schedule.
- Data export assessment when cross-border facts exist.
