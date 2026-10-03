# ADR 0004: Standards that run as checks

Status: accepted · 2026-10

## Context

Written engineering standards drift: nobody re-reads them, and reviews catch gaps late.

## Decision

Every standard that can be checked from the files is a rule in `aief check`, run in each
service's CI. Exceptions are waivers with a reason in `pyproject.toml`, reported every time.

## Consequences

- A cheap, consistent floor across every service; reviews spend their time on design.
- The checks look for evidence (a file, a step, a version bound), not quality; the release gate
  still needs people.
