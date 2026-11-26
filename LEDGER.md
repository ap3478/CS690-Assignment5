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

## Entry 3
artifact:  commit 1dfd50a, docs/spec.md section 7 "Proposed, not built" (daily limit; error
           bodies outside section 4), and decisions D5 and D8
tool:      Claude (claude.ai cloud agent session), Claude Opus 5.5 (claude-opus-5-5), 2026-11-25; main agent, no subagent
prompts:   asked whether my draft decisions met the section 7 criteria, asked for the format
           fixed and shown before commit, moved D15 and chose last-value-wins, asked to
           commit; prompts/03b-proposed-not-built.txt
review:    the daily-limit entry is mine from my draft: the page handles daily_limit but
           section 6 does not define it, so building it would reject requests the spec
           accepts. Claude flagged that my draft D15 (invalid_request with FastAPI's 404
           and 405) would change section 6, which ties invalid_request to 422; I moved it
           to "Proposed, not built" instead of deciding it. Claude also flagged that 422
           for duplicate query parameters and duplicate JSON keys (D5, D8) rejects requests
           the spec arguably accepts; I changed both to "last value wins". Claude only
           reformatted the decision lines to "- Dn." and removed my notes to myself;
           I read the final text before it was committed.
checks:    python tools/check.py: "17 decisions D1, D2, ... in spec section 7" OK;
           git diff before commit: only section 7 of docs/spec.md changed.
evidence:  HANDOUT Part 3, step 3; spec section 7 rule; sections 4 to 6 (R9, error codes)
risk:      the AGENTS.md Backend rule still asks for the R9 body on FastAPI's 404s and
           405s, which contradicts the new "Proposed, not built" entry until I fix it;
           the daily-limit entry will be superseded by R11 in Part 8.

## Entry 4
artifact:  review of the draft acceptance tests on branch tests-review, commit b57b99b
           (289 tests by the test-writer subagent), before the lock
tool:      Claude (claude.ai cloud agent session), Claude Opus 5.5 (claude-opus-5-5), 2026-11-25; main agent, no subagent
prompts:   pasted the check.py tests output, asked for the next step and for a fix list to
           give the test-writer; prompts/04a-test-review.txt
review:    Claude read all 289 tests against sections 1 to 6. The tests check status,
           error code, exact error keys and "nothing saved" throughout, but about 40
           cases tested my section 7 decisions, not the spec: D1 (1.0, 1e0), D2 (01, +1,
           " 1", fullwidth digits), D3 (empty room_id), D4 (GET check order), D5 and D8
           (last value wins), D7 (year 0000, fullwidth digits), D8 (NaN), D9
           (Content-Type, non-UTF-8), D13 (simultaneous requests), D14 (ids not reused),
           plus integers too large for SQLite. A correct backend that decided those
           differently would fail them (RUBRIC C3). Two R9 order cases used True and 9.0
           for room_id, which depend on type coercion; changed to "1" and "9". Kept the
           R4 Unicode and length tests and room_id true: Python's strip() and len() and
           JSON's boolean type make them follow from the spec.
checks:    Claude applied the same changes to a scratch copy (not pushed) and ran
           python tools/check.py tests: 247 tests, R1 2, R2 40, R3 89, R4 21, R5 31, R6 8,
           R7 13, R8 11, R9 20, R10 12; run now: 0 passed, 247 failed or errored.
evidence:  RUBRIC C1, C3, C4; spec sections 1 to 6 and section 7 D1 to D14
risk:      the review is by reading, against no backend; a test can still be wrong in a
           way only a correct backend would show. The fixes are made by the test-writer
           from the list, so its diff must be checked before the lock.

## Entry 5
artifact:  commits 7c424ac (tests/acceptance/, 247 tests for R1 to R10) and 7998c23 (deny rule
           Edit(/tests/acceptance/**) in .claude/settings.json), tag a5-tests-locked on 7998c23
tool:      Claude Code [version], test-writer subagent, 2026-11-25; review by Claude
           (claude.ai, Claude Opus 5.5), see entry 4
prompts:   the HANDOUT Part 4 prompt, the fix list from the review, and a follow-up for the
           fixes it missed; prompts/04-tests.txt
review:    the first run gave 289 tests; about 40 cases tested section 7 decisions, not
           the spec, and were removed from a list (entry 4). After the fix list the counts
           were R6 9, R7 14, R8 19, 257 in total: the R6, R7 and R8 fixes had not been
           applied, so I sent a follow-up and got 247. Missed: the two R9 order cases still
           use room_id True and 9.0 instead of "1" and "9", found only after the lock by
           comparing with the reviewed copy. They pass on a backend that follows D1, but
           fail on one that coerces types; left as locked (rule 2) and noted in REPORT Q2.
checks:    python tools/check.py tests: 247 tests, R1 2, R2 40, R3 89, R4 21, R5 31, R6 8,
           R7 13, R8 11, R9 20, R10 12; 0 passed, 247 failed or errored.
           python tools/check.py, Lock section: tag exists, deny rules in the tagged commit,
           no backend code at the tag, 247 tests, 0 passed, locked files unchanged: all OK.
evidence:  R1 to R10; tag a5-tests-locked; RUBRIC C1, C2, B2a; evidence/permission-denied.md
risk:      tests r9 r3_before_r5 and r3_before_r6 depend on how a backend treats True and
           9.0; the tests are checked against no backend yet; the deny rule does not stop
           Bash from changing a test (REPORT Q6).
