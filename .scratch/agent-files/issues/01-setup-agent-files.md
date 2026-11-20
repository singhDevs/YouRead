# Set up agent-files

Status: ready-for-agent
Type: task

## Problem

The repository needs a shared entry point for coding agents and documented
conventions for issue tracking, triage, and domain documentation.

## Scope

- Add a root `AGENTS.md` that directs agents to the relevant guidance.
- Document local Markdown tickets and specs under `.scratch/<feature>/`,
  including ticket numbering, comments, and wayfinding operations.
- Document the five default triage roles and their local status values.
- Define the single-context domain layout using root `GLOSSARY.md` and
  `docs/adr/`, including how agents should use terminology and flag conflicts.

## Acceptance criteria

- [ ] `AGENTS.md` links agents to issue-tracker, triage, and domain guidance.
- [ ] `docs/agents/issue-tracker.md` defines ticket and spec conventions.
- [ ] `docs/agents/triage-labels.md` maps all five default triage roles.
- [ ] `docs/agents/domain.md` explains the domain layout and handles missing docs.
- [ ] Commits contain only this ticket and the agent guidance files.

## Comments

- Keep release publishing, package metadata, version, CLI, and README changes
  outside this issue.
