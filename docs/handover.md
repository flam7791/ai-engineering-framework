# Handover pack

Version 0.1 · What an operating team receives before it takes over a production service. The
service is not handed over until every item is in place and the receiving team has run the
first two runbook drills with the builder.

| # | Item | Where it lives | Accepted by |
|---|---|---|---|
| 1 | Service summary: purpose, users, owner, backup, support hours | README.md | Operating team lead |
| 2 | System card: intended use, out of scope, limits, oversight | SYSTEM_CARD.md | Business owner |
| 3 | Architecture: pattern, topology, components, data flows | README.md, docs/decisions.md | Architecture |
| 4 | Threat model and accepted residual risks | THREAT_MODEL.md | Security |
| 5 | Configuration: every setting, its default and who may change it | README.md | Operating team |
| 6 | Secrets: names only, where they are stored, rotation | OPERATIONS.md | Operating team |
| 7 | Deployment: image, version, environments, how to roll back | CHANGELOG.md, release tags | Operating team |
| 8 | Monitoring: signals, thresholds, dashboards, alert routes | OPERATIONS.md | Operating team |
| 9 | Runbook: incidents, containment, kill switch, who to tell | OPERATIONS.md | Operating team |
| 10 | Evaluation: cases, latest results per model, how to re-run and record | evals/, README.md | Business owner |
| 11 | Cost: per task and per month at current volume, budget at the gateway | OPERATIONS.md | Finance contact |
| 12 | Known issues and the backlog | Issue tracker | Operating team |
| 13 | Review and retirement dates | OPERATIONS.md | Business owner |

## Knowledge transfer sessions

1. Walk-through of the code path for one request, from question to audit line.
2. Runbook drill: model endpoint down, switch to the fallback.
3. Runbook drill: a wrong answer reported, from detection to a new evaluation case.
4. Release drill: change a document, re-run the evaluation, tag, deploy, roll back.

## Support model

| Level | Who | Handles |
|---|---|---|
| 1 | Service desk | Access, "it does not answer", known issues |
| 2 | Operating team | Incidents in the runbook, configuration, releases |
| 3 | AI lab (builder) | Changes to prompts, retrieval, guardrails, models; evaluation design |
