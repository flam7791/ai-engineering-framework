# UC-030: Summarise published indicators for the monthly newsletter

**Decision (proposed): Park: no owner after launch**  
Pattern: P3 Code computes, model writes, code checks (reference: `oecd-data-pipeline`)  
Topology: **any**: public information: the cheapest adequate model, local or commercial  
Value: about 10.0 hours saved a month

| Criterion | Score (1-5) | Reason |
|---|---|---|
| feasibility | 5 | known pattern P3 |
| information sensitivity | 5 | public information |
| security | 4 | most consequential action: draft |
| cost | 5 | about 0.30 USD a month at 3.0 USD per million tokens |
| scalability | 2 | only 3 users |
| interoperability | 5 | 1 systems with APIs: statistics API |
| operational sustainability | 1 | no owner after launch |
| **average** | **3.86** | |

Model usage: about 100,000 tokens a month; at an illustrative 3.0 USD per million tokens a commercial model would cost about 0.30 USD a month.

## Controls

- Evaluation set agreed with the business owner before the pilot, run in CI
- Model calls through the gateway: team budget, audit ledger without content
- Outputs labelled as drafts; a person sends or files them

## Platform components

- C1 Model gateway: routing, budgets, personal-data masking (governed-llm-gateway)
- C2 Reference deployment: hardened containers, monitoring, runbook (governed-ai-platform)

## Conditions to resolve

- scalability: only 3 users
- operational sustainability: no owner after launch
- value: about 10.0 hours saved a month, below the 20-hour bar

_A triage aid, not a decision: the decision record is signed by the business owner and the AI lab._
