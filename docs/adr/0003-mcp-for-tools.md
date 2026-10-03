# ADR 0003: MCP for tools shared across assistants and agents

Status: accepted · 2026-10

## Context

The same data sources (statistics APIs, document libraries, registers) are wanted by several
assistants and agents. Point-to-point integrations multiply and each re-implements access rules.

## Decision

A data source used by more than one assistant or agent is exposed once as a Model Context
Protocol server. Servers are read-only by default and annotate their tools; the agent runtime
classifies MCP tools from those annotations and treats any tool not marked read-only as an
external action.

## Consequences

- One place to enforce the sensitivity ceiling, rate limits and provenance for each source.
- HTTP deployments need authentication in front of them; stdio stays local to one machine.
