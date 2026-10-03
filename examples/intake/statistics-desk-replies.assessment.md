# UC-014: Draft replies to requests for statistics

**Decision (proposed): Proceed to proof of concept**  
Pattern: P1 Governed retrieval (RAG) with a sensitivity ceiling (reference: `policy-evidence-mcp`)  
Topology: **hybrid**: internal information: commercial models in the organisation's tenant or local models, chosen per task by the gateway; personal data masked before it leaves  
Value: about 120.0 hours saved a month

| Criterion | Score (1-5) | Reason |
|---|---|---|
| feasibility | 4 | known pattern P1; low tolerance for error needs validated citations and review |
| information sensitivity | 4 | internal information |
| security | 4 | most consequential action: draft |
| cost | 5 | about 7.20 USD a month at 3.0 USD per million tokens |
| scalability | 4 | reusable across units |
| interoperability | 5 | 2 systems with APIs: document library, statistics API |
| operational sustainability | 4 | owned after launch by Statistics Desk |
| **average** | **4.29** | |

Model usage: about 2,400,000 tokens a month; at an illustrative 3.0 USD per million tokens a commercial model would cost about 7.20 USD a month.

## Controls

- Evaluation set agreed with the business owner before the pilot, run in CI
- Model calls through the gateway: team budget, audit ledger without content
- Sensitivity ceiling enforced in retrieval: nothing above internal
- Outputs labelled as drafts; a person sends or files them
- Citations or figures validated in code; failures go to a review queue

## Platform components

- C1 Model gateway: routing, budgets, personal-data masking (governed-llm-gateway)
- C2 Reference deployment: hardened containers, monitoring, runbook (governed-ai-platform)

_A triage aid, not a decision: the decision record is signed by the business owner and the AI lab._
