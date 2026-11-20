# Domain Docs

This repo uses a single-context domain layout.

## Before exploring

- Read `GLOSSARY.md` at the repo root.
- Read ADRs in `docs/adr/` relevant to the area being explored.

If these files are absent, proceed silently. Domain documentation is
created lazily by `/domain-modeling` when terms or decisions are resolved.

## File structure

- `GLOSSARY.md`: domain terminology for the repo.
- `docs/adr/NNNN-<decision>.md`: architecture decision records.

## Use the glossary's vocabulary

Use glossary terms when naming domain concepts in issue titles,
proposals, hypotheses, and tests. Respect explicitly avoided synonyms.

If a concept is missing, reconsider whether it belongs to the domain.
Note real vocabulary gaps for `/domain-modeling`.

## Flag ADR conflicts

Explicitly identify any existing ADR your proposal contradicts,
including the decision and the reason to reconsider it.
