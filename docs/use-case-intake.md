# Use-case intake

Version 0.1 · A structured first conversation with a business owner. `aief intake` scores a
proposal on seven criteria, recommends a pattern, a deployment topology and the controls it
needs, and proposes a decision. It is a triage aid: the decision record is signed by people.

## Fields

```yaml
id: UC-014
title: Draft replies to requests for statistics
owner: Head of the Statistics Desk
task: answer_from_documents      # see the list below
users: 40
uses_per_month: 600
minutes_saved_per_use: 12
tokens_per_use: 4000             # estimate; measured in the proof of concept
price_per_mtok: 3.0              # optional: from the current price list of the intended model
data:
  classification: internal       # public | internal | restricted | confidential
  personal_data: false
  source_quality: curated        # curated | mixed | unmanaged
actions: draft                   # read | draft | external
error_tolerance: low             # cost of a wrong answer: low | medium | high
systems: [document library, statistics API]
systems_have_apis: true
reusable_across_units: true
owner_after_launch: Statistics Desk
```

| `task` | Pattern |
|---|---|
| `answer_from_documents` | P1 Governed retrieval |
| `assistant_tool_access` | P2 Read-only MCP tool server |
| `data_to_text` | P3 Code computes, model writes, code checks |
| `match_or_classify` | P4 Deterministic first, model chooses among candidates |
| `multi_step_with_actions` | P5 Governed agent with approvals |
| `team_knowledge_in_assistant` | P6 Curated knowledge layer |

## Scoring (1 = unfavourable, 5 = favourable)

| Criterion | Rule | Example reason |
|---|---|---|
| Feasibility | 5, minus 1 for mixed sources, 2 for unmanaged, 1 for low error tolerance on P1/P5 | "sources are mixed (drafts next to finals)" |
| Information sensitivity | public 5, internal 4, restricted 2, confidential 1; minus 1 for personal data | "restricted information; personal data" |
| Security | read 5, draft 4, external 2; external on restricted or confidential = 1 | "external actions on restricted information" |
| Cost | Cloud/hybrid: monthly API estimate (< 50 USD = 5 … ≥ 5,000 = 1). Local: 4, or 3 if volume needs a GPU server | "about 7.20 USD a month at 3.0 USD per million tokens" |
| Scalability | 3, +1 reusable across units, +1 for 50+ users, −1 under 5 users | "reusable across units" |
| Interoperability | No systems 5; systems with APIs 5 (≤ 2) or 4; without APIs 2 | "2 systems with APIs" |
| Operational sustainability | Owner after launch 4 (5 if error tolerance is high); none = 1 | "no owner after launch" |

Value (hours saved a month) is reported beside the scores, not blended in, so a valuable but
risky case is visible as exactly that.

## Topology follows the data

| Data | Topology | Gateway policy |
|---|---|---|
| Restricted or confidential | **local**: open-weight models on own infrastructure only | `local_only` |
| Internal with personal data | **hybrid** | `local_if_pii` and masking |
| Internal | **hybrid** | masking |
| Public | **any**: cheapest adequate model | default routing |

## Proposed decision

1. No owner after launch → **Park**.
2. Any criterion at 1 → **Proceed only with conditions** (the conditions are listed).
3. Average ≥ 3.5 and ≥ 20 hours saved a month → **Proceed to proof of concept**.
4. Average ≥ 2.5 → **Proceed with conditions**.
5. Otherwise → **Park**.

## Examples

| File | Decision | Why |
|---|---|---|
| [statistics-desk-replies](../examples/intake/statistics-desk-replies.assessment.md) | Proceed to proof of concept | Curated sources, drafts only, 120 hours a month |
| [staff-case-routing](../examples/intake/staff-case-routing.assessment.md) | Proceed only with conditions | Restricted personal data and an agent that would send replies: local models, four eyes |
| [newsletter-summaries](../examples/intake/newsletter-summaries.assessment.md) | Park | Nobody owns it after launch |

The thresholds are starting values. Calibrate them against the first ten real decisions and
record the change in the [changelog](../CHANGELOG.md).
