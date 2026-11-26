# Provenance Ledger

Write one entry per reviewable change, when the work is done, using exactly the schema
in HANDOUT.md. Put the prompts you typed into AI tools in `prompts/` and name the file in
the entry's `prompts` field. When a subagent did the work, name it in the `tool` field.

## Worked example (not graded; leave it here and add your entries under "My entries")

This shows the level of detail expected. The change is not part of this assignment, and
the commit SHA, date and numbers are made up.

```
## Entry 0
artifact:  commit 3f9c2ab, GET /api/health in app/routes.py (example only)
tool:      Claude Code 2.1.x, main agent, Claude Opus model, 2031-03-01
prompts:   asked for a health endpoint that returns {"ok": true}; prompts/00-health.txt
review:    read the diff. The agent also added a "version" field and a new package to
           read it from git; I rejected both because the request did not ask for them,
           and kept only the endpoint.
checks:    python -m pytest: 41 passed. python tools/check_layers.py: passed.
evidence:  request from the operations team, ticket OPS-12
risk:      no test checks the endpoint under load; not needed for this change.
```

## My entries


## Entry 1
artifact:  commit 3f3ebbc, AGENTS.md "Backend rules" section (Part 1)
tool:      Claude (claude.ai cloud agent session), Claude Opus 5.5 (claude-opus-5-5), 2026-11-25; main agent, no subagent
prompts:   asked Claude to draft the Backend rules for me to review before committing; prompts/01-backend-rules.txt
review:    read the draft against the six points Part 1 requires (layers, create_app,
           R9 error body, sqlite3 with no ORM, one connection per call, checks after
           every task). Kept three extra rules: validate POST by hand in R9 order,
           never coerce types for room_id, a failed request changes nothing. Committed
           the draft without rewording it; the leading "- " of the first bullet was
           lost when pasting. Rejected nothing.
checks:    python tools/check.py: "AGENTS.md, Backend rules: 20 lines (at least 6)" OK;
           section is under the 30-line limit.
evidence:  HANDOUT Part 1; RUBRIC B1; spec sections 3, R3 to R9
risk:      the wording is the AI draft, not yet rewritten in my own words (RUBRIC B1);
           the rules are requests to the model, not enforced (only
           .claude/settings.json is); /permissions not yet re-checked after this commit.
