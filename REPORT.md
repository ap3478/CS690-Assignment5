# Assignment 5 report

Name: Aditya P
Agent tool and version (Claude Code or Antigravity CLI): Claude Code [version: run `claude --version`]; some steps were done with Claude (claude.ai, Claude Opus 5.5), as the ledger records

Answer each question in two to five sentences, below the question, unless it asks for a
table. Point to commits, files, tests or rule IDs where you can.

## 1. Clarify (Part 3)

How many questions did the agent list? Which one, if guessed wrong, would have changed
the backend's behavior the most, and what did you decide?

DRAFT: check every sentence against what you did.

The agent listed [N] questions (prompts/03-clarify.txt). [Some, name them] were already
answered by the spec; the rest became decisions D1 to D17 in docs/spec.md section 7
(commit 1dfd50a), and two went to "Proposed, not built": the daily limit and error bodies
outside section 4. The question that would have changed behavior most is whether
`room_id: "1"` or `1.0` counts as an integer (R3): FastAPI accepts both by default, so
an agent guessing silently would have saved bookings the spec should reject. I decided
in D1 that only a JSON number with no decimal point or exponent is an integer, and wrote
it into the Backend rules in AGENTS.md so the agent validates by hand.


## 2. Tests before the lock (Part 4)

Name one weak test you found before the lock and how you fixed it. Did any locked test
turn out to be wrong later? If so, which test, which rule, and why.

DRAFT: the second half can only be answered after Part 6.

The first draft had 289 tests, and about 40 cases tested my section 7 decisions instead
of sections 1 to 6 (ledger entry 4). For example, test_r8_ids_are_not_reused_after_cancel
expected a new booking never to get a cancelled id (D14), but section 2 only forbids two
*current* bookings sharing an id, so a correct backend using plain SQLite ids would fail
it. The test-writer removed these from a list, leaving 247 tests that all failed at the
lock (tag a5-tests-locked). Two R9 order cases, r3_before_r5 and r3_before_r6, use
`room_id: True` and `9.0`; the fix to use the strings "1" and "9" was missed and only
found after the lock. They pass on a backend that follows D1, but a correct backend that
coerces `true` to 1 or `9.0` to 9 reports a later rule, so they check something sections
1 to 6 do not clearly fix. They stay as locked. [After Part 6: did any other locked test
turn out to be wrong?]


## 3. The plan (Part 5)

What did you reject from the plan, or add to "Not in this change", and why?

DRAFT: check every sentence against what you did.

The plan's "Not in this change" already excluded what the spec does not ask for: R11
and daily_limit, the R9 error body for unknown paths and wrong methods (spec section 7,
"Proposed, not built"), pydantic request models, new packages, an ORM, login, capacity
and past-date checks, CORS, and any edit to frontend/ or tests/acceptance/, so there was
nothing outside the spec to reject. Reading it against the spec, I sent four revisions
in plan mode (prompts/05-plan.txt, prompt 2): format checks use `re.fullmatch`, because
in Python `$` also matches before a final newline, so "2031-03-14\n" or "1\n" would have
passed R2 and R3; the repository is one class, `Repository(db_path)`, instead of an open
choice; room checks use the ids from `repo.list_rooms()` instead of a hard-coded 1 to 4,
so a huge integer never reaches SQLite; and connections use `isolation_level=None`, so
`BEGIN IMMEDIATE` works. The plan builds D13 in Task 1 (`create_booking_if_free`), so the
ADR in Part 9 records a decision already in the code.

## 4. Review findings (Part 7)

One row for every finding in `evidence/review.md` and `evidence/contract-check.md`.

| # | Agent | Finding, in a few words | Fixed (commit SHA) or rejected (reason) |
|---|---|---|---|
| 1 | | | |

## 5. The spec change (Part 8)

Did the contract checker, or any earlier step, notice that the page already handles an
error code the spec did not define? Why does a change go spec, then test, then code, in
three commits?

## 6. Where the lock stops (Part 4)

Name one way an agent could still change a locked test despite your deny rule, and what
in this assignment would catch it.

DRAFT

The rule `Edit(/tests/acceptance/**)` in .claude/settings.json blocks Claude Code's
file-editing tools, but not shell commands: an agent with Bash could change a test with
`sed -i` or a short Python script, and the deny rules for Bash only cover `git push` and
`rm -rf`. The grader would catch it, because it compares every file that was in
tests/acceptance/ at the tag a5-tests-locked with the submitted commit
(`python tools/check.py` reports "locked test files unchanged since the lock"). Reading
`git diff` after every agent task, before committing, catches it earlier.


## 7. Legacy parser (Part 10)

Which odd behaviors did you pin? Did the agent's first refactor change any behavior, and
how did you find out? Before fixing one of these bugs for real, what would you check?

## 8. The agent team

What did giving each agent one job and its own tools buy you? Name one thing that went
wrong with an agent and how you caught it.

## Screenshot

`evidence/page.png` shows the page with at least one booking made through your backend.
