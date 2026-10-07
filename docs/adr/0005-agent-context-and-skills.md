# ADR 0005: Context files for coding agents, and skills for tool repositories

Status: accepted · 2026-10

## Context

Most changes to these repositories are now made with a coding agent in the loop. Each agent
starts cold: it rediscovers the commands, and it does not know which rules are load-bearing
(the sensitivity ceiling, "the model chooses but never writes an identifier", "an external
action waits for a person"). A source-level study of eleven production coding agents found
that all the systems that manage repository context have converged on auto-discovered Markdown
context files, and that the newer ones read each other's file names (`AGENTS.md`,
`CLAUDE.md`). The same study found
skills (a `SKILL.md` with instructions loaded on demand) slightly ahead of MCP in adoption,
with MCP kept for integrations that run as a process ([Barbaste et al., 2026][harness],
Recommendations 6 and 14).

## Decision

- Every repository has an `AGENTS.md` at the root: the commands CI runs, the layout, the
  invariants nobody may weaken, and the working rules (failures become evaluation cases,
  recordings are re-recorded rather than edited). `CLAUDE.md` contains only `@AGENTS.md`, so
  there is one source. `aief check` rule ENG-17 (SHOULD) looks for it and for a command in it.
- A repository that agents call as a tool (an MCP server or a CLI) also ships a skill under
  `skills/<name>/SKILL.md`: when to use the tool, the call sequence, how to read the result,
  and what not to claim from it. MCP stays the transport; the skill is the know-how.
- The template generates both files, so a new service passes ENG-17 on day one.

## Consequences

- An agent working on a repository is told the guardrails before it touches them; a review can
  point to the line it broke.
- Two more files to keep current. The commands in `AGENTS.md` are copied from CI; when CI
  changes, `AGENTS.md` changes in the same commit.
- The check proves the file exists and names a command, not that the invariants are right;
  that stays a review question.

[harness]: https://arxiv.org/abs/2609.00006
