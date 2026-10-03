# UC-021: Route staff support cases and draft first responses

**Decision (proposed): Proceed only with conditions**  
Pattern: P5 Governed agent with policy engine and human approval (reference: `governed-agents`)  
Topology: **local**: restricted information: open-weight models on the organisation's own infrastructure only (gateway policy local_only)  
Value: about 120.0 hours saved a month

| Criterion | Score (1-5) | Reason |
|---|---|---|
| feasibility | 3 | known pattern P5; sources are mixed (drafts next to finals); low tolerance for error needs validated citations and review |
| information sensitivity | 1 | restricted information; personal data |
| security | 1 | most consequential action: external; external actions on restricted information |
| cost | 4 | no per-use API cost; volume fits a shared CPU or small GPU |
| scalability | 3 | 12 users, one unit |
| interoperability | 4 | 3 systems with APIs: case system, email, policy library |
| operational sustainability | 4 | owned after launch by Staff Services |
| **average** | **2.86** | |

Model usage: about 5,400,000 tokens a month; at an illustrative 3.0 USD per million tokens a commercial model would cost about 16.20 USD a month.

## Controls

- Evaluation set agreed with the business owner before the pilot, run in CI
- Model calls through the gateway: team budget, audit ledger without content
- Gateway policy local_only: no route to an external provider exists
- Every external action approved by a named person (four eyes)
- Egress allow-list for recipients and endpoints
- Citations or figures validated in code; failures go to a review queue
- Policy engine on every tool call, step and cost budgets, kill switch

## Platform components

- C1 Model gateway: routing, budgets, personal-data masking (governed-llm-gateway)
- C2 Reference deployment: hardened containers, monitoring, runbook (governed-ai-platform)

## Conditions to resolve

- information sensitivity: restricted information; personal data
- security: most consequential action: external; external actions on restricted information

_A triage aid, not a decision: the decision record is signed by the business owner and the AI lab._
