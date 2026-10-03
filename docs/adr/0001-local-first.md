# ADR 0001: Local first

Status: accepted · 2026-10

## Context

Much of what an international organisation would use AI for involves internal or restricted
information. External model APIs need a contract, a data-protection assessment and a residency
answer before the first test, and they bill per use. Open-weight models now pass many routine
tasks (classification, extraction, grounded short answers, wording from computed data) on modest
hardware.

## Decision

Every pattern has a path that runs entirely on the organisation's infrastructure, and generated
services default to a local open-weight model. Commercial models are used where the data allows
and the evaluation shows the gain is worth the cost, through the gateway.

## Consequences

- Proofs of concept can start on day one, on any laptop, with no procurement.
- Restricted use cases are possible at all.
- Quality and latency are lower for some tasks on small hardware; the evaluation makes the gap
  visible per use case instead of assumed.
- The organisation needs the skills to run model servers; the reference deployment and runbook
  reduce, not remove, that cost.
