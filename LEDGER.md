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
risk:      the Backend rules are requests the model can ignore; only the permission
           rules in .claude/settings.json are enforced by the tool. The error-body rule
           asked for the R9 body on FastAPI's 404s and 405s, which section 6 has no code
           for; I narrowed it to the section 4 endpoints in c259cb4. The first bullet's
           missing space was fixed in 07c6f22.
## Entry 2
artifact:  Part 3 clarify step: question list Q1 to Q22 (no files changed); decisions
           go in docs/spec.md section 7, commit "Spec clarified"
tool:      Claude (claude.ai cloud agent session), Claude Opus 5.5 (claude-opus-5-5), 2026-11-25; main agent, no subagent
prompts:   the Part 3 clarify prompt from HANDOUT.md, word for word; prompts/03-clarify.txt
review:    Claude listed 22 questions touching R2, R3, R4, R6, R7, R8, R9, R10 and
           sections 3 and 6. Claude itself noted Q3, Q6 and Q14 may already be answered
           by the spec. Q21 (the page handles daily_limit, which section 6 does not
           define) goes under "Proposed, not built", not a decision.
           From the list I wrote D1 to D17 in section 7 (commit 1dfd50a, entry 3). A few
           were close to the spec's own text, such as an empty date= (D3) and rooms
           already in the file (D17), but I wrote them down so the agent would not
           guess. Q21 (daily_limit) and the error body for unknown paths and wrong
           methods went under "Proposed, not built". The Q numbers I cite in the
           decisions do not match this list's numbering.
checks:    Claude made no file edits while answering. After section 7 was written:
           python tools/check.py: "17 decisions D1, D2, ... in spec section 7" OK.
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
tool:      Claude Code with Claude Opus 5.5 (claude-opus-5-5), test-writer subagent, 2026-11-25; review by Claude
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

## Entry 6
artifact:  commit b227636, app/repository.py (Part 6, Task 1 of docs/plan.md)
tool:      Claude Code with Claude Opus 5.5 (claude-opus-5-5), main agent, 2026-11-25; review by Claude (claude.ai,
           Claude Opus 5.5)
prompts:   the HANDOUT Part 6 task prompt for Task 1; prompts/06-task1.txt
review:    the agent wrote one file and touched nothing else (git status: only
           app/repository.py). It ran its checks with .venv/bin/python because python is
           not on my PATH and python3 is 3.9; I now activate the venv before starting
           Claude Code. Read against the plan and the spec: Repository(db_path) opens a
           new connection per call with isolation_level=None and closes it; tables are
           created if missing and the four rooms added only when rooms is empty (D17);
           bookings use AUTOINCREMENT (D14); list order is room_id, then start (R2); the
           overlap test is start < new end AND new start < end for the same room and date
           (R7), so touching bookings pass; check and insert run in one BEGIN IMMEDIATE
           transaction with ROLLBACK on overlap and on any exception (D13); "start" and
           "end" are quoted because END is an SQL keyword. I relied on this review for the line-by-line reading.
           Nothing rejected.
checks:    python tools/check_layers.py: FAILED only on L4 (main.py, routes.py, service.py,
           models.py missing), as the plan expects. python -m pytest tests/acceptance -q:
           9 failed, 238 errors, 0 passed (No module named 'app.main'). Claude's smoke
           test of the committed file: init_db twice gives 4 rooms; overlap, containing
           and touching cases; other room; order; delete True then False; new id larger
           after a delete; 20 threads booking the same slot gave exactly 1 booking.
evidence:  R1, R2, R7, R8, R10; D13, D14, D17; docs/plan.md Task 1; AGENTS.md Backend rules
risk:      delete_booking and list_bookings raise OverflowError for integers beyond
           SQLite's 64-bit range; the plan makes the service filter those first (Task 2),
           so this must be checked there. No acceptance test can run until Task 3.

## Entry 7
artifact:  commit cd027ca (docs/spec.md section 7, decision D18) and commit a7950b0,
           app/models.py and app/service.py (Part 6, Task 2 of docs/plan.md)
tool:      Claude Code with Claude Opus 5.5 (claude-opus-5-5), main agent, 2026-11-25;
           review by Claude (claude.ai, Claude Opus 5.5)
prompts:   the HANDOUT Part 6 task prompt for Task 2, then a prompt to implement D18;
           prompts/06-task2.txt
review:    the agent stopped and asked about a name sent as the JSON escape "\ud800" (an
           unpaired surrogate): it is valid JSON and passes R3 to R6, but SQLite cannot
           store it, so it would have become a 500. Of invalid_request (R3), invalid_name
           (R4) and leaving it, I chose invalid_request: it matches D9 (a body that is not
           valid UTF-8) and does not contradict D12 (any characters allowed in a name).
           I wrote D18 into the spec and committed it before the code. The agent also
           handled integers too long to convert, which the plan did not spell out: a huge
           room_id is room_not_found and a huge booking id is booking_not_found, and
           neither reaches SQLite (the risk left by entry 6). Read against the plan: R3
           to R7 checked by hand in R9 order with re.fullmatch; room ids compared with
           repo.list_rooms(); bool and 1.0 rejected (D1); NaN rejected (D8); nothing saved
           before the last check. Minor: the invalid_request message repeats the page's
           own sentence ("The request was not valid.") when the page shows both; left for
           the Part 7 review. I relied on this review for the line-by-line reading.
checks:    python tools/check_layers.py: FAILED only on L4 (main.py, routes.py missing), as
           the plan expects. python -m pytest tests/acceptance: 9 failed, 238 errors,
           0 passed (No module named 'app.main'). Claude's smoke test of the committed
           service: R3, R4, R5, R6 and R7 cases, the R9 order cases, "\ud800", NaN, a
           trailing newline in dates and ids, 01 and huge room ids, delete ids abc, -1,
           30 and 5000 digits: every result as the spec and D1 to D18 say.
evidence:  R2 to R9; D1, D2, D4, D5, D7, D8, D9, D13, D18; docs/plan.md Task 2
risk:      no HTTP test runs until Task 3; the service was tested only by direct calls.

## Entry 8
artifact:  commit ee4d21d, app/routes.py and app/main.py (Part 6, Task 3 of docs/plan.md);
           commit 67c6e93, evidence/page.png
tool:      Claude Code with Claude Opus 5.5 (claude-opus-5-5), main agent, 2026-11-25;
           review by Claude (claude.ai, Claude Opus 5.5)
prompts:   the HANDOUT Part 6 task prompt for Task 3; prompts/06-task3.txt
review:    the agent wrote the two files and touched nothing else. Read against the plan:
           routes import the service, never the repository (L3); the POST body is read as
           raw bytes and query and path values as strings, so FastAPI never coerces them
           (D1, D2); repeated query parameters use the last value (D5); a ServiceError
           becomes exactly {"error", "message"} (R9); FastAPI's own 422s get the R9 body,
           and unknown paths and wrong methods keep FastAPI's defaults (section 7,
           "Proposed, not built"); /, /app.js and /styles.css are served from a path built
           from __file__. The agent added run_in_threadpool so blocking database calls do
           not stall other requests; accepted, it changes no behavior. Noted for the Part 7
           review: FastAPI also serves /docs, /redoc and /openapi.json by default, which
           section 4 does not list. On the page I booked Quiet Room A 09:00 to 10:00, tried
           09:00 to 09:30 in the same room and got the overlap message, and cancelled a
           booking (screenshot evidence/page.png). I relied on this review for the line-by-line reading.
checks:    python tools/check_layers.py: "Layer check passed: L1 to L5 hold."
           python -m pytest: 247 passed. python tools/check.py: every check for Parts 1
           to 6 OK, including "3 commits change app/ between the lock and the R11 code".
           The agent also checked: page files served as text/html, text/javascript and
           text/css; room_id=1%0A and DELETE /api/bookings/1%0A give invalid_request;
           16 simultaneous identical bookings gave one 201 and fifteen 409 overlap.
evidence:  R1 to R10; D1, D2, D5, D13, D16; docs/plan.md Task 3; evidence/page.png
risk:      the tests run through TestClient, not a real server with several workers;
           /docs, /redoc and /openapi.json are endpoints the spec does not list.

## Entry 9
artifact:  commit 2c0d9d7 (evidence/review.md, evidence/contract-check.md) and commit
           a057cd9 (fixes for review findings 2, 3 and 4 in app/repository.py,
           app/main.py, app/service.py); REPORT.md question 4
tool:      Claude Code with Claude Opus 5.5 (claude-opus-5-5), main agent with the
           reviewer and contract-checker subagents, 2026-11-25; Claude (claude.ai,
           Claude Opus 5.5) suggested an answer for each finding
prompts:   the HANDOUT Part 7 review prompt, then the fix prompts; prompts/07-reviews.txt
review:    the reviewer found no blocking break of R1 to R10 or L1 to L5 and returned four
           findings; the contract checker matched every request, field and section 6
           code, with two mismatches, both on the page. Rejected: reviewer 1 (an unpaired
           surrogate in an ignored field gets 201; R3 ignores unlisted fields and nothing
           is stored), contract #19 (daily_limit, not in the spec until R11) and contract
           #20 (404 from GET /api/rooms, not in the spec). Fixed: reviewer 2 (busy timeout
           30 s, so queued bookings wait instead of a 500), 3 (docs endpoints off) and 4
           (docstring). The three fixes went into one commit instead of one each.
           I relied on this review for the line-by-line reading.
checks:    after a057cd9: python -m pytest: 247 passed; python tools/check_layers.py:
           L1 to L5 hold; GET /docs, /redoc and /openapi.json give 404, GET / gives 200.
evidence:  R3, R7, R9, R11 (proposed); D13, D18; evidence/review.md; evidence/contract-check.md
risk:      the reviewers only read code and ran nothing; the busy-timeout fix is not
           covered by a test; a cosmetic missing space remains in repository.py
           (BOOKING_COLUMNS ='...').

## Entry 10
artifact:  R11 daily limit: commits 32eb55d (spec), 76ce428
           (tests/acceptance/test_r11_daily_limit.py), 767023f (app/repository.py,
           app/service.py), 5a4dcfa (spec D19), a9eb2c9 (second review run),
           9596dac (docstrings)
tool:      Claude Code with Claude Opus 5.5 (claude-opus-5-5), main agent, 2026-11-26;
           the spec edits and the draft of the R11 tests by Claude (claude.ai, Claude
           Opus 5.5)
prompts:   the HANDOUT Part 8 code prompt and the follow-ups; prompts/08-r11-code.txt;
           spec and test drafts in prompts/08a-r11-spec.txt
review:    spec first (32eb55d, the HANDOUT text), then the test, which I put in
           tests/acceptance/ myself: Claude drafted 8 tests and I checked each expected
           value against R11; before the code, 2 failed with 201 instead of 409, 6 passed.
           The code: the service supplies the policy (names trimmed and case folded,
           at most 2) and the repository counts the person's bookings on that date inside
           the same BEGIN IMMEDIATE transaction as the overlap check, after it (R9 order
           R7 then R11, and D13 still holds). Names are compared in Python with
           casefold(), not SQLite's ASCII-only lower(); I recorded that choice as D19,
           but committed it after the code instead of before. The locked test
           test_r7_same_person_back_to_back_is_allowed now fails: it books one person
           three times on one date, which R11 forbids, so it stays failing (REPORT Q2).
           I relied on this review for the line-by-line reading.
checks:    python tools/check.py: R11 in spec, the spec commit and the test commit both
           before the code commit, 8 test_r11_ tests, 19 decisions: all OK.
           python -m pytest: 254 passed, 1 failed (test_r7_same_person_back_to_back_is_allowed,
           409 daily_limit instead of 201). python tools/check_layers.py: L1 to L5 hold.
evidence:  R11, R7, R9, P4, D13, D19; evidence/review-r11.md; evidence/contract-check-r11.md
risk:      the locked R7 test will also fail on a correct reference backend; the
           daily-limit count reads every booking on the date into Python, fine at
           library scale; D19 came after the code it describes.

## Entry 11
artifact:  commit 4399080, tests/legacy/test_old_format.py (35 characterization tests);
           commit 05f74ba, refactored legacy/old_format.py (Part 10)
tool:      Claude (claude.ai, Claude Opus 5.5) drafted the tests, 2026-11-26; Claude Code
           with Claude Opus 5.5 (claude-opus-5-5), main agent, did the refactor,
           2026-11-26 (not the test-writer: its rules forbid values from running code)
prompts:   the HANDOUT Part 10 refactor prompt; prompts/10-legacy.txt
review:    the tests pin what the code does today, right or wrong, with "# BUG: pinned,
           not fixed" above each wrong result: 12 PM becomes 24, 12 AM stays 12, 13 PM
           becomes 25, lowercase pm and a double space lose PM, 9:5 is not padded, a
           three-digit year is kept, a fourth date part is ignored, only the first letter
           of a name changes. Every exception is pinned with its class (IndexError,
           ValueError, KeyError). I checked the values against python -m legacy.old_format
           legacy/old_bookings.csv. The refactor: type hints and docstrings on both
           functions, named constants, and day.split("/") and the clock split done once
           and indexed, not unpacked, so a short or long date still raises or behaves as
           before. The agent's first refactor passed all 35 tests unchanged.
checks:    python -m pytest tests/legacy: 35 passed, before and after the refactor.
           python tools/check.py, Legacy: 35 tests, pass on the refactored file, type
           hints on every function: OK. Claude also checked: the 35 tests pass on the
           original course file; they caught all of 20 copies of the original with one
           behavior changed each (for example .capitalize(), .split() with no argument,
           unpacking the date, fixing 12 PM); the original and the refactored file gave
           the same result or exception on 120,000 random inputs.
evidence:  tests/legacy/test_old_format.py; legacy/old_format.py; HANDOUT Part 10
risk:      the pinned bugs are still bugs; before importing old bookings they must be
           fixed on purpose, with the matching tests changed in the same commit.
