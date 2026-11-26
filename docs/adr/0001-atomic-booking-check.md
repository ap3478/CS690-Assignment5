# ADR 0001: Check and save each booking in one SQLite write transaction

Status: Accepted
Date: 2026-11-26

## Context

FastAPI runs requests on several threads, and every repository call opens its own
SQLite connection. A booking is valid only if nothing else changes the bookings table
between the checks and the insert: R7 (no overlap in the same room and date) and,
since spec version 2, R11 (at most two bookings per person per date). If the check and
the insert are separate steps, two requests that arrive at the same moment can both
find no clash and both insert. Then two overlapping bookings exist (R7 broken), or a
person gets a third booking (R11 broken). No acceptance test shows this, because the
tests send one request at a time. Spec decision D13 says the check and the save happen
as one step, so exactly one of two such requests succeeds and the other gets 409.

## Options considered

1. One write transaction in the repository: `create_booking_if_free` opens a connection
   with `isolation_level=None`, runs `BEGIN IMMEDIATE`, checks for an overlap, counts
   the person's bookings on that date, inserts, and commits, or rolls back on a clash.
   Advantage: SQLite takes the write lock at `BEGIN IMMEDIATE`, so it holds across
   threads and across separate processes (for example several uvicorn workers) on the
   same file. Cost: all bookings are written one at a time, and the overlap and
   daily-limit checks have to run inside the repository's transaction rather than
   entirely in the service.
2. A `threading.Lock` in the service around "check, then insert". Advantage: simple,
   and the rules stay entirely in `service.py`. Cost: it only works inside one Python
   process; a second process or worker on the same database file is not covered.
3. A SQLite `BEFORE INSERT` trigger that raises an error when the new booking overlaps.
   Advantage: the database enforces the rule even for writes that bypass the
   application. Cost: a business rule moves into SQL, R11's case-folded name
   comparison does not fit in SQLite's ASCII-only `lower()`, and the error must be
   mapped back to `overlap` or  `daily_limit`.
4. A slots table with one row per room, date and 30-minute slot, and a UNIQUE
   constraint. Advantage: the database rejects double bookings by itself. Cost: a
   larger schema, many rows per booking, cancelling must delete every slot, and it
   does not cover R11 at all.

## Decision

Option 1, built in commit b227636 (Task 1) and extended for R11 in 767023f.
`Repository.create_booking_if_free` does the overlap check, then the daily-limit
count, then the insert, inside one `BEGIN IMMEDIATE` transaction. The service supplies
the policy (how names are compared and the limit of two) and turns the result into the
`overlap` or `daily_limit` error. It is the only option that covers both R7 and R11,
holds across processes, and adds no package or extra table.

## Consequences

- Easier: the rule holds under concurrent requests. In a smoke test, 20 threads booking
  the same slot produced exactly one booking. Any process that writes through
  `Repository` is covered.
- Harder: writes are serialized. A request waits up to 30 seconds for the lock
  (`timeout` set in commit a057cd9, review finding 2). If it still cannot get the lock,
  the request fails with a plain 500, which the spec does not define (R11 review,
  finding 9). The overlap and daily-limit logic sits in `repository.py`, which a
  reviewer flagged against the Backend rule that the service enforces every rule
  (R11 review, finding 7).
- Watch: any new rule that depends on existing bookings must be checked inside this
  same transaction, or the race comes back. No automated acceptance test covers this
  race, so a change to `create_booking_if_free` needs a concurrency check by hand.
