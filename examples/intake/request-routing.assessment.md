# UC-027: Route incoming requests for input to the right unit

**Decision (proposed): Proceed to proof of concept**  
Pattern: P7 Bounded judgment: a typed decision from a closed answer set, people below the threshold (reference: `reference-resolver-agent`)  
Topology: **hybrid**: internal information: commercial models in the organisation's tenant or local models, chosen per task by the gateway; personal data masked before it leaves  
Value: about 75.0 hours saved a month

| Criterion | Score (1-5) | Reason |
|---|---|---|
| feasibility | 5 | known pattern P7 |
| information sensitivity | 4 | internal information |
| security | 4 | most consequential action: draft |
| cost | 5 | about 4.05 USD a month at 3.0 USD per million tokens |
| scalability | 4 | reusable across units |
| interoperability | 5 | 2 systems with APIs: mailbox, request tracker |
| operational sustainability | 4 | owned after launch by Secretariat |
| **average** | **4.43** | |

Model usage: about 1,350,000 tokens a month; at an illustrative 3.0 USD per million tokens a commercial model would cost about 4.05 USD a month.

## Controls

- Evaluation set agreed with the business owner before the pilot, run in CI
- Model calls through the gateway: team budget, audit ledger without content
- Outputs labelled as drafts; a person sends or files them
- The model answers from a closed set (a schema enum); anything else counts as no decision and goes to a person
- Acceptance thresholds calibrated on a labelled set before the pilot: accuracy per confidence band reported in every evaluation
- Hard rules (permissions, policy, exact restrictions) run before the model's judgment and are never replaced by it

## Platform components

- C1 Model gateway: routing, budgets, personal-data masking (governed-llm-gateway)
- C2 Reference deployment: hardened containers, monitoring, runbook (governed-ai-platform)

_A triage aid, not a decision: the decision record is signed by the business owner and the AI lab._
