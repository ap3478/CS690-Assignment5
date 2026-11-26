# Plan: RoomBook backend (spec R1–R10) in three tasks

## Context

`app/` holds only `__init__.py`. The acceptance tests in `tests/acceptance/` (R1–R10)
are committed and locked. The goal is a backend that matches `docs/spec.md`
(sections 2–7, including decisions D1–D17), keeps the layer rules in AGENTS.md /
`tools/check_layers.py` (L1–L5), makes every acceptance test pass without editing it,
and leaves `frontend/` unchanged.

**What the tests can show at each stage:** every acceptance test goes through the
`client` / `new_client` fixtures in `tests/conftest.py`, and those import
`app.main.create_app`. So **no acceptance test can pass until Task 3 is done**. Tasks 1
and 2 are checked with throwaway `python -c` smoke checks (no new test files) and with
the parts of `check_layers.py` that apply. The full suite is the gate at the end of
Task 3.

Packages: only the ones in `requirements.txt` (fastapi, uvicorn, httpx, pytest) plus the
standard library (`sqlite3`, `json`, `re`, `datetime`).

---

## Task 1

Files: `app/repository.py`

**Creates:** `app/repository.py` (the only module that imports `sqlite3` or holds SQL).

**Contents**
- `class Repository`, built as `Repository(db_path)`, with a private `_connect()`
  that opens a **new connection for each call** with `sqlite3.connect(db_path,
  isolation_level=None)` (autocommit, so the repository runs its own transactions) and
  closes it in `finally` / `contextlib.closing`. Connections are never shared.
- `init_db()`: `CREATE TABLE IF NOT EXISTS rooms(id INTEGER PRIMARY KEY, name TEXT,
  capacity INTEGER)` and `bookings(id INTEGER PRIMARY KEY AUTOINCREMENT, room_id, date,
  start, end, booked_by)`. `AUTOINCREMENT` means ids are never reused (D14). Insert the
  four rooms from spec §2 **only if `rooms` has no rows** (D17).
- `list_rooms()` → rows ordered by `id`.
- `list_bookings(date, room_id=None)` → `ORDER BY room_id, start`. Zero-padded
  `HH:MM` sorts correctly as text.
- `create_booking_if_free(room_id, date, start, end, booked_by) -> dict | None`: one
  connection; runs `BEGIN IMMEDIATE` itself, then the overlap query (`room_id=? AND
  date=? AND start < ?new_end AND ?new_start < end`), then the insert if there's no
  clash, then `COMMIT`. On overlap it runs `ROLLBACK` and returns `None`. On any
  exception it runs `ROLLBACK` and re-raises. Returns the new row on success. Because the
  check and the save are one locked step, D13 holds.
- `delete_booking(id) -> bool` (True if a row was deleted).
- Return plain dicts/tuples; the service turns them into models.

**Done when**
- The file exists and imports only the standard library.
- Smoke check against a temp db file: `init_db()` twice → exactly 4 rooms; create,
  list, overlap→`None`, touching bookings allowed, delete→True then False, a new id after
  a delete is larger than the old one.
- `check_layers.py`: no L1/L3/L5 problems. (L4 still reports the missing modules; that
  is expected until Task 3.)
- Acceptance tests: **none pass yet** (no `app.main`).

---

## Task 2

Files: `app/models.py` and `app/service.py`

**Creates:** `app/models.py`, `app/service.py`. Neither imports fastapi/starlette (L2)
or sqlite3 (L1).

**`app/models.py`** (dataclasses, no pydantic validation)
- `Room(id, name, capacity)`, `Booking(id, room_id, date, start, end, booked_by)`,
  `BookingRequest(room_id: int, date: str, start: str, end: str, booked_by: str)` (the
  shape after validation), each with `to_dict()` that gives exactly the spec §4 fields.

**`app/service.py`**
- `class ServiceError(Exception)` with `status`, `code`, `message`. Messages are short
  plain-English sentences (D15). Only the six §6 codes are used.
- `class BookingService(repo)` with:
  - `list_rooms()` — R1.
  - `list_bookings(date_raw: str | None, room_id_raw: str | None)` — R2 in D4 order:
    date (missing, empty per D3, `re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", v)` and a
    real day via `datetime.date`, years 0001–9999 per D7) → room_id format (D2,
    `re.fullmatch(r"-?[0-9]+", v)`, empty → invalid per D3) → room exists: the integer
    is checked against the ids from `repo.list_rooms()`, never passed to SQLite, so huge
    values are simply `room_not_found`.
  - Every format check (date, time, room_id, booking id) uses `re.fullmatch`, never
    `^...$`, so values with a trailing newline such as `"2031-03-14\n"` or `"1\n"` are
    rejected.
  - `create_booking(raw_body: bytes)` — parses and validates **by hand in R9 order**,
    stopping at the first rule broken:
    - **R3:** decode UTF-8 (on failure → invalid_request, D9); `json.loads` with
      `parse_constant` raising so NaN/Infinity are rejected (D8; duplicate keys: last
      wins by default). Body must be a `dict`. All five keys present. `room_id`:
      `type(v) is int` (rejects bool, float like 1.0/1e0, str; D1). The other four:
      `type(v) is str`. `date` as in R2. `start`/`end`:
      `re.fullmatch(r"[0-9]{2}:[0-9]{2}", v)` with hour ≤ 23 and minute ≤ 59. Unknown keys ignored.
    - **R4:** `name = booked_by.strip()`; `1 <= len(name) <= 40` (code points, D10–D12).
    - **R5:** minutes in {00, 30}; start ≥ 08:00; end ≤ 22:00; start < end;
      duration ≤ 180 min.
    - **R6:** room_id must be in the set of ids from `repo.list_rooms()`; the integer
      itself never reaches SQLite in this check.
    - **R7:** `repo.create_booking_if_free(...)`; `None` → `409 overlap`.
    - Returns a `Booking` with the trimmed name.
  - `cancel_booking(id_raw: str)` — R8: D2 format via `re.fullmatch(r"-?[0-9]+", v)`,
    otherwise invalid_request; an integer
    outside SQLite's int64 range → `booking_not_found` without querying; else
    `repo.delete_booking`, False → `booking_not_found`.
- Nothing is written before every check passes, so a failed request changes nothing
  (R9).

**Done when**
- Smoke checks call the service directly (temp db) and cover: one valid booking; one case
  per row of the R9 `CASES` table giving the expected code; `room_id` values `"1"`, `1.0`,
  `True`, NaN; date `2031-02-29` rejected and `2032-02-29` accepted; DELETE ids `"abc"`,
  `"1.0"`, `"-1"`, and a 30-digit id.
- `check_layers.py`: only L4 complaints left (routes.py / main.py missing).
- Acceptance tests: **still none pass** (no `app.main`).

---

## Task 3

Files: `app/routes.py` and `app/main.py`

**Creates:** `app/routes.py`, `app/main.py`.

**`app/routes.py`** (HTTP only, calls the service, never imports the repository — L3)
- `build_router(service) -> APIRouter`, or the routes registered with the service read
  from `request.app.state.service`.
- `GET /api/rooms` → 200 list.
- `GET /api/bookings` → read `request.query_params.getlist("date")[-1]` (last value,
  D5; `None` when missing) and the same for `room_id`; ignore other params (D6).
- `POST /api/bookings` → `body = await request.body()`, pass the raw bytes to the
  service, return `JSONResponse(..., 201)`. No pydantic body model, so FastAPI never
  validates or coerces.
- `DELETE /api/bookings/{booking_id}` with `booking_id: str` (no int conversion) →
  `Response(status_code=204)` with an empty body.
- Turns `ServiceError` into `JSONResponse({"error": code, "message": message}, status)`.

**`app/main.py`**
- `create_app(db_path: str = "roombook.db") -> FastAPI`: builds `Repository(db_path)`,
  calls `init_db()`, builds the service, includes the router.
- Registers a `RequestValidationError` handler that returns
  `{"error": "invalid_request", "message": ...}` with 422, so FastAPI's own 422s also
  have the R9 shape. Unknown paths and wrong methods keep FastAPI's defaults (spec §7
  Q18).
- Serves `GET /`, `/app.js`, `/styles.css` with `FileResponse` from
  `Path(__file__).parent.parent / "frontend"` using the right media types (D16). No
  `StaticFiles` mount, so no other paths are exposed.
- `uvicorn app.main:create_app --factory` works.

**Done when**
- `python tools/check_layers.py` → "Layer check passed: L1 to L5 hold."
- `python -m pytest` → **all acceptance tests pass**: R1 (`test_r1_rooms.py`), R2
  (`test_r2_list.py`), R3 (`test_r3_shape.py`), R4 (`test_r4_name.py`), R5
  (`test_r5_times.py`), R6 (`test_r6_room.py`), R7 (`test_r7_overlap.py`), R8
  (`test_r8_cancel.py`), R9 (`test_r9_errors.py`), R10 (`test_r10_app.py`).
  The only allowed skip is the one already built into `test_r8_integer_matching_no_booking`.
- `git status` shows no changes under `frontend/` or `tests/acceptance/`.
- Optional: run the `contract-checker` and `reviewer` agents for a read-only cross-check.

---

## Not in this change

- **R11 / daily limit** (`daily_limit` error): listed under spec §7 "Proposed, not
  built". The backend never sends it.
- R9 error bodies for unknown paths, wrong methods or trailing-slash paths: these keep
  FastAPI's defaults (§7 Q18).
- Any edit to `frontend/`, `tests/acceptance/`, `tests/conftest.py`, `requirements.txt`
  or `tools/`.
- New endpoints, fields, error codes, auth, capacity checks (P2), past-date checks (P1),
  CORS, logging or config.
- New packages, an ORM or pydantic request models.
- New test files. Tasks 1–2 are checked with throwaway smoke commands only.
- Commits: only if you ask for them after each task.

## Verification (end to end)

1. `python tools/check_layers.py` → passes L1–L5.
2. `python -m pytest` → all pass; report the counts.
3. Manual: `uvicorn app.main:create_app --factory --port 8000`, open
   `http://localhost:8000/`, book, list and cancel through the page.
