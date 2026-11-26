# Assignment 5 report

Name: Aditya P
Agent tool and version (Claude Code or Antigravity CLI): Claude Code, model Claude Opus 5.5 (claude-opus-5-5); some steps were done with Claude (claude.ai, Claude Opus 5.5), as the ledger records

Answer each question in two to five sentences, below the question, unless it asks for a
table. Point to commits, files, tests or rule IDs where you can.

## 1. Clarify (Part 3)

How many questions did the agent list? Which one, if guessed wrong, would have changed
the backend's behavior the most, and what did you decide?

The agent listed 22 questions (prompts/03-clarify.txt). A few were close
to what the spec already says, such as whether an empty `date=` is valid and what
`create_app` does with rooms already in the file, but I still wrote them down (D3, D17)
so the agent would not guess; in all, the answers became D1 to D17 in docs/spec.md
section 7 (commit 1dfd50a), and two went to "Proposed, not built": the daily limit and
the error body for unknown paths and wrong methods. The question that would have changed
behavior most is whether `room_id: "1"`, `1.0` or `true` counts as an integer (R3):
FastAPI accepts them by default, so an agent guessing silently would have saved bookings
the spec should reject. I decided in D1 that only a JSON number with no decimal point or
exponent is an integer, and the Backend rules in AGENTS.md tell the agent to validate by
hand and never coerce types.

## 2. Tests before the lock (Part 4)

Name one weak test you found before the lock and how you fixed it. Did any locked test
turn out to be wrong later? If so, which test, which rule, and why.

The test-writer's first run produced 289 tests, and about 40 cases tested my section 7
decisions instead of sections 1 to 6 (ledger entry 4). For example,
test_r8_ids_are_not_reused_after_cancel expected a cancelled id never to come back (D14),
but section 2 only forbids two current bookings sharing an id, so a correct backend using
plain SQLite ids would fail it; the test-writer deleted these from a list, leaving 247
tests that all failed at the lock (tag a5-tests-locked, commit 7998c23). Two locked tests
are weak: the R9 order cases r3_before_r5 and r3_before_r6 still use `room_id: True` and
`9.0` because that fix was missed before the lock; they pass on my backend (D1), but a
correct backend that coerces those values would report a later rule. One locked test
turned out wrong after the spec changed: test_r7_same_person_back_to_back_is_allowed
(R7, P4) books one person three times on one date, which R11 (spec version 2) now
rejects with 409 daily_limit, so it stays failing and the code was not bent to pass it
(python -m pytest: 254 passed, 1 failed).

## 3. The plan (Part 5)

What did you reject from the plan, or add to "Not in this change", and why?

The plan's "Not in this change" already excluded what the spec does not ask for: R11 and
daily_limit, the R9 error body for unknown paths and wrong methods ("Proposed, not
built"), pydantic request models, new packages, an ORM, login, capacity and past-date
checks, CORS, and any edit to frontend/ or tests/acceptance/, so there was nothing
outside the spec to reject. Reading it against the spec, I sent four revisions in plan
mode (prompts/05-plan.txt, prompt 2): format checks use `re.fullmatch`, because in Python
`$` also matches before a final newline, so "2031-03-14\n" or "1\n" would have passed R2
and R3; the repository is one class, `Repository(db_path)`; room checks use the ids from
`repo.list_rooms()` instead of a hard-coded 1 to 4, so a huge integer never reaches
SQLite; and connections use `isolation_level=None`, so `BEGIN IMMEDIATE` works. The plan
builds D13 in Task 1, so ADR 0001 records a decision already in the code.

## 4. Review findings (Part 7)

One row for every finding in `evidence/review.md` and `evidence/contract-check.md`.

| # | Agent | Finding, in a few words | Fixed (commit SHA) or rejected (reason) |
|---|---|---|---|
| 1 | reviewer | D18 checks only the five spec fields, so "\ud800" in an ignored field still gets 201 | Rejected: R3 says fields not listed are ignored and D18 covers the fields R3 checks; the ignored field is never stored, so nothing fails |
| 2 | reviewer | SQLite's 5-second busy timeout can turn a queued POST into a 500 "database is locked" | Fixed in a057cd9: connections wait up to 30 seconds for the write lock |
| 3 | reviewer | FastAPI serves /docs, /redoc and /openapi.json, which section 4 does not list | Fixed in a057cd9: all three turned off in create_app |
| 4 | reviewer | service.py docstring says D1 to D17, but D18 is implemented | Fixed in a057cd9 |
| 5 | contract-checker | #19: the page handles daily_limit, the backend never sends it | Rejected: not in the spec (section 7, "Proposed, not built"); R11 adds it in Part 8 |
| 6 | contract-checker | #20: the page handles a 404 from GET /api/rooms | Rejected: not in the spec; R1 defines only 200, and the page's branch is for when no backend runs |

After R11 both agents ran again (evidence/review-r11.md, evidence/contract-check-r11.md):

| # | Agent | Finding, in a few words | Fixed (commit SHA) or rejected (reason) |
|---|---|---|---|
| 7 | reviewer (R11 run) | Overlap and daily-limit decisions run in repository.py, not service.py | Rejected: D13 needs the check and the save in one BEGIN IMMEDIATE transaction; the service supplies the policy (person_key, max_per_person) and maps the outcome to the error |
| 8 | reviewer (R11 run) | "\ud800" in an ignored field still gets 201 | Rejected: same as finding 1 |
| 9 | reviewer (R11 run) | A lock held over 30 s gives a plain 500 | Rejected: not in the spec; section 6 has no code for a server error |
| 10 | reviewer (R11 run) | models.py docstring out of date after R11 | Fixed in 9596dac |
| 11 | reviewer (R11 run) | service.py class docstring says R1 to R9 | Fixed in 9596dac |
| 12 | contract-checker (R11 run) | #3: the page handles a 404 from GET /api/rooms | Rejected: not in the spec (same as finding 6) |

The three accepted findings from the first run were fixed in one commit, a057cd9, rather
than one commit each as Part 7 asks. Every other row of both contract checks is a match.

## 5. The spec change (Part 8)

Did the contract checker, or any earlier step, notice that the page already handles an
error code the spec did not define? Why does a change go spec, then test, then code, in
three commits?

Yes, twice before R11 existed: the Part 3 clarify step listed it, and I put it under
"Proposed, not built" instead of deciding it; then the contract checker reported it as
mismatch #19, and I rejected that finding as "not in the spec" (Q4, row 5). Spec first
(32eb55d) means the rule is agreed in writing before anyone builds it. The test next
(76ce428) shows the rule is missing, failing for the right reason (201 instead of 409)
before any code exists, and the code last (767023f) makes it pass, so three commits let
a reader and the grader check the order. I broke this order once: D19 (case folding)
went into the spec after the code that uses it (5a4dcfa).

## 6. Where the lock stops (Part 4)

Name one way an agent could still change a locked test despite your deny rule, and what
in this assignment would catch it.

The rule `Edit(/tests/acceptance/**)` in .claude/settings.json blocks Claude Code's
file-editing tools, but not shell commands: an agent with Bash could change a test with
`sed -i` or a short Python script, and my Bash deny rules only cover `git push` and
`rm -rf`. Claude Code itself pointed this out when the edit was refused, offering a
`sed` command, which I did not run (evidence/permission-denied.md). The grader would
catch such a change, because it compares every file that was in tests/acceptance/ at the
tag a5-tests-locked with the submitted commit (`python tools/check.py` reports "locked
test files unchanged since the lock"); reading `git diff` after every agent task catches
it earlier.

## 7. Legacy parser (Part 10)

Which odd behaviors did you pin? Did the agent's first refactor change any behavior, and
how did you find out? Before fixing one of these bugs for real, what would you check?

tests/legacy/test_old_format.py pins 35 behaviors, including these wrong ones, each
marked "# BUG: pinned, not fixed": 12:15 PM becomes 24:15, 12:00 AM stays 12:00, 13:00 PM
becomes 25:00, "3:00 pm" and "9:00  PM" (two spaces) lose the PM, "9:5" keeps one minute
digit, a three-digit year is kept as is, and only the first letter of a name changes
("mcDonald" becomes "McDonald"); it also pins every exception with its class
(IndexError, ValueError, KeyError). The agent's first refactor passed all 35
tests unchanged (commit 05f74ba), so no behavior changed. The likely trap was "remove
the repeated split calls": unpacking `month, d, year = day.split("/")` would raise
ValueError instead of IndexError and break a four-part date, and `.split()` with no
argument would fix the double-space bug by accident; the refactor indexes one split
instead, and the tests also caught all 20 one-change copies of the original we tried.
Before fixing a bug for real I would check which rows of the real export hit it and what
the new backend's R3 and R5 say about the result (24:15 is rejected by R3), then change
the pinned test and the code in the same commit.

## 8. The agent team

What did giving each agent one job and its own tools buy you? Name one thing that went
wrong with an agent and how you caught it.

One job each kept each agent honest: the test-writer could write tests but not, after
the lock, change them, and the reviewer and contract checker could only read, so they
reported problems instead of quietly "fixing" them, and every finding needed my answer
(Q4). The contract checker found what tests cannot: two things the page expects that the
spec does not define. The standing rules helped too: in Task 2 the main agent stopped
and asked about an unpaired surrogate in a name instead of guessing, which became D18.
What went wrong: the test-writer's first run tested my section 7 decisions in about 40
cases, and its fix run skipped the R6, R7 and R8 changes. I caught the first by reading
the tests against the spec before the lock (ledger entry 4), and the second because
`python tools/check.py tests` showed 257 tests instead of the expected 247.

## Screenshot

`evidence/page.png` shows the page with at least one booking made through your backend.
