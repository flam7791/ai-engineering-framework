# Engineering standards

Version 0.2 · The minimum bar for any AI service. **MUST** rules block a release; **SHOULD**
rules are expected, and an exception is recorded as a waiver with its reason.

Rules marked ✓ are checked automatically by `aief check`. The check looks for evidence that a
practice is in place; a review still decides whether it is done well.

## Checked rules

| Rule | Level | Standard | What the check looks for |
|---|---|---|---|
| ENG-01 ✓ | MUST | README with a quick start | README with a quick start / how-to-run section |
| ENG-02 ✓ | MUST | Automated tests | `tests/test_*.py`, or an end-to-end test script |
| ENG-03 ✓ | MUST | CI runs the tests | A workflow that runs them |
| ENG-04 ✓ | MUST | No secrets in the repository | Key patterns (Anthropic, OpenAI, AWS, GitHub, private keys, Azure storage) and committed `.env` files |
| ENG-05 ✓ | MUST | Evaluation set | Files under `evals/` |
| ENG-06 ✓ | MUST | CI runs the evaluation as a gate | An evaluation step in CI |
| ENG-07 ✓ | MUST | Runtime dependencies versioned | Every runtime dependency in `pyproject.toml` has a version bound |
| ENG-08 ✓ | MUST | Containers run as a non-root user | A non-root `USER` in every Dockerfile |
| ENG-09 ✓ | SHOULD | Runs without a commercial API | A documented local path (Ollama, vLLM, llama.cpp, OpenAI-compatible endpoint) |
| ENG-10 ✓ | SHOULD | Design decisions recorded | `docs/*decisions*.md` or `docs/adr/` |
| ENG-11 ✓ | SHOULD | Operating notes | `OPERATIONS.md` or a runbook |
| ENG-12 ✓ | SHOULD | System card | `SYSTEM_CARD.md`: intended use, limits, evaluation, oversight |
| ENG-13 ✓ | SHOULD | Dependency updates automated | Dependabot or Renovate configuration |
| ENG-14 ✓ | SHOULD | Dependency vulnerability scan in CI | `pip-audit`, OSV-Scanner, Trivy, Grype or CodeQL in CI |
| ENG-15 ✓ | SHOULD | Changelog | `CHANGELOG.md` |
| ENG-16 ✓ | SHOULD | Licence | A `LICENSE` file (internal services usually waive it) |
| ENG-17 ✓ | SHOULD | Context file for coding agents | `AGENTS.md` (or `CLAUDE.md`) at the root that names a command to run: tests, lint, evaluation ([ADR 0005](adr/0005-agent-context-and-skills.md)) |

## Practices reviewed, not checked

**Design**

- Start from a pattern in the [catalogue](patterns.md); record departures in the decisions file.
- The topology follows the data classification ([intake](use-case-intake.md)).
- Deterministic code for anything that can be written as a rule; the model only where reading,
  judgement or wording is needed.
- Where the model only has to decide (a category, a candidate, a yes/no), use pattern P7: a
  closed answer set, thresholds calibrated on a gold set, a person below the threshold.
- `AGENTS.md` states the invariants nobody may weaken, not only the commands; a tool repository
  that agents will call ships a `SKILL.md` saying when and how to use it.

**Models**

- Talk to models through the OpenAI-compatible API, normally through the gateway.
- Temperature 0 for anything evaluated; record the model name and version in results.
- A model change (including a new tag of the same local model) re-runs the evaluation.

**Data and security**

- Documents above the service's ceiling are not loaded, not merely filtered.
- Content from documents and tools is treated as data; outputs that act or link are validated
  in code.
- No content in logs; a hash or id is enough to investigate.
- Secrets from the environment or a secret store; a local model needs none.
- External actions need a named person's approval.

**Evaluation**

- Cases agreed with the business owner before the pilot, including at least: two real
  questions, one not covered by any example, one out of scope, one planted instruction, one
  above-ceiling document.
- Deterministic checks rather than a model grading a model, where possible.
- Live runs are recorded and replayed in CI; simulated or stand-in results never pass a
  production gate on their own.

**Operations**

- An owner and a backup before the pilot starts.
- Cost per task known before production, for the model that will run in production.
- Every confirmed failure becomes an evaluation case before the fix ships.

## Waivers

```toml
[tool.aief.waivers]
ENG-16 = "Internal service: not published under an open-source licence"
```

A waiver is reported in every check with its reason. Review waivers at each release gate.
