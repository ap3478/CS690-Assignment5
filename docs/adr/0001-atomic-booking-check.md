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
   mapped back to `overlap` or
