No, two requests arriving at the same moment can't both pass the check. The check and the insert happen inside one locked database step, so the second request has to wait for the first to finish.

**How it works now** (`app/repository.py:90-137`):

1. `create_booking_if_free` opens its own connection and runs `BEGIN IMMEDIATE` (line 109) **before** it reads anything. That takes SQLite's single write lock for the whole file straight away.
2. A second request that reaches line 109 meanwhile can't get the lock. It waits, for up to the 30-second timeout set at line 36.
3. The first request runs the overlap check (line 112), then the daily-limit count (line 122), then the `INSERT` (line 129), and `COMMIT`s (line 134).
4. Only then does the second request get the lock. Its overlap check now sees the new row, and it gets `409 overlap`.

When I sent the same booking 16 times at once, exactly 1 got `201` and 15 got `409`. The same pattern held for the daily limit: 12 bookings at once gave 2 × `201`.

**What makes it safe**

- **One step:** the service calls a single repository method (`service.py:217`). If it called "check" and "insert" as two separate repository calls, each on its own connection, two requests could both pass the check before either inserted.
- **Lock before reading:** `BEGIN IMMEDIATE` takes the lock first. With a plain `BEGIN`, both requests could read at the same time, and the clash would only show up when one tries to write.
- **Known weak spot:** a request that waits longer than 30 seconds gets `database is locked`, which comes back as a 500.

**Ways to prevent the race with SQLite**

| # | Approach | Advantage | Cost |
|---|---|---|---|
| 1 | **`BEGIN IMMEDIATE`, check then insert** (what we use) | Simple, and the rules stay in Python. The loser waits, then gets a proper `409`. | All writes to the file queue behind one lock, including cancels on other dates. Past the timeout, the result is a 500. |
| 2 | **`BEGIN EXCLUSIVE`** | Strongest lock: nothing else can read or write during the step. | In SQLite's default journal mode it also blocks every reader, such as `GET /api/bookings`, so there's less concurrency and no extra safety over #1. |
| 3 | **Plain `BEGIN` (deferred) plus retry** | Reads still happen side by side until the first write. | The loser fails with `SQLITE_BUSY` when it tries to write; its 30-second wait doesn't help here. You need a retry loop. |
| 4 | **One statement: `INSERT … SELECT … WHERE NOT EXISTS (overlapping row)`** | A single statement is atomic in SQLite, so no explicit transaction is needed. | When nothing is inserted you can't tell overlap from daily limit without another query. Case folding can't be done in SQL either, because SQLite's `LOWER()` only handles A–Z; you'd have to register a Python function. |
| 5 | **A trigger: `BEFORE INSERT … RAISE(ABORT, 'overlap')`** | The database enforces the rule for every writer, even tools outside this app. | The rule moves into the schema and away from `service.py`, against AGENTS.md. The error has to be recognised by its message text, and existing database files need the trigger added. |
| 6 | **A slots table with `UNIQUE(room_id, date, slot)`**, one row per 30-minute slot | A database constraint rules out double booking outright, whatever the transaction handling. | Schema change, up to 6 rows per booking, cancel must remove the slots, and it does nothing for the daily limit. |
| 7 | **A Python `threading.Lock` around check and insert** | No database lock waits, and it's easy to follow. | It only protects one process. A second uvicorn worker or another program using the same file gets around it, so you still need #1 underneath. |
| 8 | **WAL mode (`PRAGMA journal_mode=WAL`) together with #1** | Readers no longer wait while a booking is being written, so `GET`s stay fast under load. | It adds `-wal` and `-shm` files next to the database, and the setting stays in the file permanently. Writes still go one at a time. |

**Recommendation:** keep #1. It's what D13 asks for, the rules stay in the service, and the loser always gets the right code. If load ever matters, add #8 so reads don't wait behind writes. The only gap left is the timeout 500, and fixing it needs a spec decision about which error to send.

I didn't edit any files.
