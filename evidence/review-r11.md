I found no blocking problems in `app/`. I have five minor findings, most severe first. The task format allows one line per finding, so each line names the failing input in the problem text.

1. /Users/ga/cs690/cs690-assignment5/app/repository.py:117 | R7, R11 (AGENTS.md "service.py enforces every rule in section 5") | minor | The overlap decision (the SQL at 111-119) and the daily-limit count and comparison (120-127) run inside the repository, not the service; this was likely done so D13 runs as one locked step, but it is against the Backend rule (input: any third same-day booking such as `{"room_id":2,"date":"2031-03-14","start":"12:00","end":"13:00","booked_by":"ana"}` after two "Ana" bookings is rejected by `repository.py:125`, not by `service.py`).
2. /Users/ga/cs690/cs690-assignment5/app/service.py:189 | R3/D18 | minor (unsure) | The unpaired-surrogate check covers only the four listed string fields, so `{"room_id":1,"date":"2031-03-14","start":"09:00","end":"10:00","booked_by":"Ana","x":"\ud800"}`, or an object key containing `\ud800`, gets 201; it is unclear whether D18 ("a string field ... the body gives 422", "the same as a body that is not valid UTF-8") reaches past R3's "fields not listed here are ignored".
3. /Users/ga/cs690/cs690-assignment5/app/repository.py:109 | R9/D15 | minor (unsure) | If `BEGIN IMMEDIATE` still cannot get the write lock after the 30 s busy timeout, `sqlite3.OperationalError` escapes as a plain-text 500 "Internal Server Error", not the `{"error","message"}` body; section 6 has no 5xx code, so the spec does not say what should happen (input: a POST while another process holds a write lock on the file for over 30 s).
4. /Users/ga/cs690/cs690-assignment5/app/models.py:44 | R11 | minor | The docstring says "Only the overlap check (R7) is left", but R11 is also checked after `BookingRequest` is built, so the comment is out of date.
5. /Users/ga/cs690/cs690-assignment5/app/service.py:131 | R11 | minor | The class docstring says "Enforces R1 to R9", but the class also enforces R11, so the comment is out of date.

What I checked and found correct:
- **R1:** rooms are ordered by id.
- **R2 and D2 to D7:**
  - The last value of a repeated parameter is used, via `getlist()[-1]`.
  - An empty `date=` or `room_id=` gives 422.
  - Checks run in D4 order: date, then room_id format, then room exists.
  - `01` and `-1` count as integers; `+1` and ` 1` give 422.
  - An integer too large for the database gives 404, not 500.
  - Only ASCII digits are accepted, and year 0000 is rejected.
- **R3 and D1, D8, D9, D18 for the listed fields:**
  - `true`, `1.0`, `1e0` and `"1"` give 422.
  - NaN and Infinity are rejected, and duplicate keys keep the last value.
  - Invalid UTF-8 and very deep nesting give 422.
- **R4 and D10 to D12:** the name is trimmed with `str.strip()`, its length is counted in code points, and the trimmed name is stored.
- **R5:** all four time conditions are enforced at the right boundaries (08:00, 22:00, start before end, 180 minutes).
- **R6:** a very long integer `room_id` gives 404.
- **R7:** the overlap test is `start < other end AND other start < end`, so bookings that only touch are allowed.
- **R11 and D19:** names are trimmed and compared with `casefold()` across all rooms, and the limit is checked after R7.
- **R8 and D14:** DELETE behaves as R8 says, and AUTOINCREMENT means an id is never reused.
- **R9:**
  - The POST checks run in the order R3, R4, R5, R6, R7, R11.
  - Every ServiceError uses the exact error body.
  - Nothing is saved before all checks pass, and a failure rolls back.
  - FastAPI's own 422s are mapped to `invalid_request`.
- **R10, D16 and D17:** the tables and rooms are created only if missing, and the three page files are served with the right media types.
- **D13:** the check and the save happen together under `BEGIN IMMEDIATE`.
- **Connections:** each repository method opens and closes its own connection.
- **Layers L1 to L5:** no violations. SQL and `sqlite3` are only in `repository.py`. `fastapi` and `starlette` are only in `routes.py` and `main.py`. Routes import only the service. All five files exist, `main.py` defines `create_app`, and no ORM is used.
- **Things built that the spec does not ask for:** none that matter. Turning off `/docs`, `/redoc` and `/openapi.json` at `main.py:28` only removes default routes, and the spec defines none of them.

I could not run `python tools/check_layers.py` or `python -m pytest` because I have no shell, so this review is based on reading the code only.

Files read: 7 (`docs/spec.md` and the six files in `app/`, including the empty `__init__.py`).
