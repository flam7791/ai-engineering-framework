# AGENTS.md: ai-engineering-framework

Instructions for coding agents (and people) changing this repository. Read this first.

The framework layer of the portfolio: reference architecture, pattern catalogue, engineering
standards checked by `aief check`, use-case intake (`aief intake`) and a Copier template for a
governed, local-first answer service. It contains no model calls of its own.

## Commands

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check .
pytest                                   # standards, intake, template rendering
for f in examples/intake/*.yaml; do aief intake "$f" | diff - "${f%.yaml}.assessment.md"; done
aief check --strict .                    # the framework meets its own standards
```

The template job in CI renders the template and runs the generated service's own checks:

```bash
copier copy --defaults --trust --vcs-ref HEAD . /tmp/svc
cd /tmp/svc && pip install -e ".[dev]" && ruff check . && pytest && policy-answers eval --model standin && aief check --strict .
```

`--vcs-ref HEAD` renders the last commit, so commit template changes before checking them.

## Layout

- `src/aief/standards.py`: one `Rule` per checked standard; `docs/standards.md` is the same list in prose
- `src/aief/intake.py`: scoring, topology and pattern recommendation; golden outputs in `examples/intake/*.assessment.md`
- `docs/patterns.md`: P1 to P7 and the two platform components, each with a reference implementation
- `docs/adr/`: decisions; `template/`: the Copier template (`*.jinja` files are rendered)

## Invariants: never weaken these

1. **A rule in `standards.py` and its row in `docs/standards.md` change together**, with a test
   in `tests/test_standards.py` for pass and fail.
2. **The generated service passes `aief check --strict` on day one** (`test_template.py`). A new
   rule needs the template to meet it in the same change.
3. **Restricted information always lands on the local topology, and an external action always
   adds a named person's approval** in the intake. Never relax these to change an assessment.
4. **Golden assessments change only with the scoring.** If `aief intake` output changes,
   regenerate the `.assessment.md` file in the same commit and say why in the changelog.
5. **Claims about the portfolio are measured.** The README table comes from running
   `aief check` on each repository; never edit counts by hand.

## Working rules

- Examples use the fictional Aurora Institute. Never add an employer's internal material.
- Record every change in `CHANGELOG.md`; a design change gets an ADR.
- British spelling (organisation, licence) and plain sentences, as in the existing docs.
- Commits carry no AI co-author trailers.
