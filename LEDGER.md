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
risk:      
## Entry 2
artifact:  Part 3 clarify step: question list Q1 to Q22 (no files changed); decisions
           go in docs/spec.md section 7, commit "Spec clarified"
tool:      Claude (claude.ai cloud agent session), Claude Opus 5.5 (claude-opus-5-5), 2026-11-25; main agent, no subagent
prompts:   the Part 3 clarify prompt from HANDOUT.md, word for word; prompts/03-clarify.txt
review:    Claude listed 22 questions touching R2, R3, R4, R6, R7, R8, R9, R10 and
           sections 3 and 6. Claude itself noted Q3, Q6 and Q14 may already be answered
           by the spec. Q21 (the page handles daily_limit, which section 6 does not
           define) goes under "Proposed, not built", not a decision.
           (Update when section 7 is written: which questions the spec answers and
           where, which became D1, D2, ..., and which I rejected.)
checks:    none run yet; Claude made no file edits while answering. (Update with python tools/check.py
           decision count after section 7 is written.)
evidence:  HANDOUT Part 3; RUBRIC D3b; spec section 7; rules R2 to R10
risk:      decisions not yet written; the question list may miss open questions that
           only show up while building or testing.
