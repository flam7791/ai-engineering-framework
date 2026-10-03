# Operations: the framework itself

Owner: AI Lab engineering lead · Backup: _name_ · Review: every three months

## Change process

1. A change to a standard, pattern or threshold is proposed as a pull request with the reason
   and, for thresholds, the decisions it would have changed.
2. Template changes must keep `aief check --strict` green on the rendered service (CI enforces it).
3. Rule changes that would fail existing services are introduced as SHOULD for one release,
   then promoted to MUST.

## Release

- Semantic versions; tags `vX.Y.Z`; notes in CHANGELOG.md.
- Services record the template version in `.copier-answers.yml` and update with `copier update`.

## Monitoring

| Signal | Source | Frequency | Action when |
|---|---|---|---|
| Services passing MUST rules | `aief check` across repositories (CI job `portfolio`) | each push, monthly review | any service failing for two weeks |
| Waivers per rule | `aief check --format json` | quarterly | a waiver used by most services: fix the rule or the template |
| Intake decisions vs. outcomes | intake files and decision records | quarterly | thresholds recalibrated |

## Retirement of a rule or pattern

Mark it deprecated in the changelog for one release, then remove it.
