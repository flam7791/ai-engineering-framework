# Changelog

## Unreleased

- Pattern P7's reranker row uses the 40-question run of policy-evidence-mcp: hit@1 0.70 to
  0.78 and hit@3 0.90 to 0.95, with 29 of 43 hybrid searches getting no decision. The third
  lesson adds: measure on enough cases.

## 0.2.1 (2026-10)

- Pattern P7 carries the measured results of its three uses (resolver adjudication, evidence
  reranker, gateway judged router) and what they share: stated confidence carried no
  information; the closed answer set and code-side corroboration did the work; the judged router
  lost to the rules and stays off.

## 0.2.0 (2026-10)

- Pattern P7, bounded judgment: a typed decision from a closed answer set, with hard rules
  first, calibrated thresholds and a person below them; intake task `decide_from_closed_set`
  and a fourth example (`request-routing`). P4 and P7 assessments now list the closed-set and
  calibration controls.
- Standard ENG-17 (SHOULD): an `AGENTS.md` (or `CLAUDE.md`) at the root that names a command to
  run ([ADR 0005](docs/adr/0005-agent-context-and-skills.md)); the template generates
  `AGENTS.md` and a `CLAUDE.md` that imports it. Standards version 0.2.
- `AGENTS.md` for this repository.

## 0.1.1 (2026-10)

- Measured results with Llama 3.1 8B across the reference implementations (docs/model-selection.md, docs/results/).

## 0.1.0 (2026-10)

- Reference architecture, six patterns, two platform components.
- Engineering standards ENG-01 to ENG-16, checked by `aief check`, with waivers.
- Use-case intake scoring on seven criteria, with topology and controls (`aief intake`).
- Lifecycle gates, model selection guide, handover pack, four ADRs.
- Copier template: local-first governed answer service (P1).
