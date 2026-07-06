# Domain: Cybersecurity

Use this file for network security, API security, access control, logs, prompt/document leakage, model abuse, and incident response.

## Review Areas

- Authentication, authorization, least privilege, and admin access.
- Secrets management and API key handling.
- Encryption in transit and at rest.
- Logs, audit trails, retention, and tamper resistance.
- Prompt/upload handling and data leakage controls.
- Abuse prevention: scraping, prompt injection, jailbreaks, spam, fraud, automated attacks.
- Vulnerability management and dependency review.
- Incident response, breach notification, and customer/regulator communication.

## AI-Specific Cyber Risks

- Prompt injection against RAG or tool-using systems.
- Model output leaking confidential snippets.
- Training or retrieval corpus poisoning.
- API abuse causing unauthorized extraction or excessive costs.
- Model supply-chain risk from third-party weights, plugins, tools, or datasets.

## Minimum Controls

- Access control matrix.
- Security logging and monitoring.
- Data isolation for tenants/customers.
- Secure deletion process.
- Incident response owner and runbook.
- Vendor security evidence for model/API providers.
- Pre-launch adversarial testing for user-facing AI.

## Escalation

Escalate to L3/L4 when a user-facing system processes confidential or personal data and lacks access controls, logging, vendor security evidence, or incident response.
