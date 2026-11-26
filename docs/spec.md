# RoomBook backend specification

Version 1. This file is the source of truth for the backend. Tests, reviews and commits
point at the rule IDs in section 5 (R1 to R11).

## 1. What the backend does

RoomBook lets library users book study rooms in 30-minute steps. The page in `frontend/`
is finished and belongs to another team. It calls the HTTP API in section 4 and nothing
else. The backend owns the rooms and the bookings, stores them in SQLite, and enforces
every rule in section 5. The page checks nothing itself, so the backend is the only place
a rule is enforced.

There are no user accounts. A booking records the name the person typed.

## 2. Data

**Rooms.** The backend has exactly these four rooms. They never change.

| id | name | capacity |
|---|---|---|
| 1 | Quiet Room A | 2 |
| 2 | Quiet Room B | 2 |
| 3 | Group Room C | 6 |
| 4 | Group Room D | 8 |

**Bookings.** A booking has these fields.

| Field | Type | Meaning |
|---|---|---|
| `id` | integer | Assigned by the backend. No two current bookings share an id. |
| `room_id` | integer | One of the room ids above. |
| `date` | string | The day, as `YYYY-MM-DD`, for example `2031-03-14`. |
| `start` | string | Start time, as `HH:MM` in 24-hour time, for example `09:30`. |
| `end` | string | End time, in the same format. |
| `booked_by` | string | The name as typed, with leading and trailing whitespace removed. |

All times are library local time. There are no time zones.

A booking covers the time from `start` up to, but not including, `end`. So 09:00 to
10:00 and 10:00 to 11:00 do not overlap.

## 3. Starting the backend

`app/main.py` defines `create_app(db_path: str = "roombook.db")`, which returns a FastAPI
application. Tests call it with a path to a fresh database file for each test.

When it is called, `create_app`:

- creates the tables in the SQLite file at `db_path` if they do not exist yet, and adds
  the four rooms if the file has no rooms yet;
- serves the page: `GET /` returns `frontend/index.html`, and `GET /app.js` and
  `GET /styles.css` return those files from `frontend/`;
- keeps all data in that one file. Two applications created with different `db_path`
  values never share data, and calling `create_app` again with the same path sees the
  data already saved there.

To run the backend and the page together:

```
uvicorn app.main:create_app --factory --port 8000
```

## 4. API

Every request and response body is JSON, except the empty body of a `204` response.

In a response, a **booking** is an object with exactly six fields: `id`, `room_id`,
`date`, `start`, `end`, `booked_by`. A **room** is an object with exactly three fields:
`id`, `name`, `capacity`.

| Method and path | Success | Rules |
|---|---|---|
| `GET /api/rooms` | `200`, a list of rooms | R1 |
| `GET /api/bookings?date=YYYY-MM-DD` | `200`, a list of bookings | R2 |
| `GET /api/bookings?date=YYYY-MM-DD&room_id=N` | `200`, a list of bookings | R2 |
| `POST /api/bookings` | `201`, the new booking | R3 to R7 |
| `DELETE /api/bookings/{id}` | `204`, empty body | R8 |

The body of `POST /api/bookings` is an object with five fields:

```json
{"room_id": 1, "date": "2031-03-14", "start": "09:00", "end": "10:30", "booked_by": "Ana"}
```

## 5. Rules

**R1. List rooms.** `GET /api/rooms` returns the four rooms in section 2, ordered by `id`
from 1 to 4.

**R2. List bookings.** `GET /api/bookings` returns the bookings on the given date, ordered
by `room_id`, then by `start`. A date with no bookings gives an empty list.
- `date` is required. It must be exactly `YYYY-MM-DD` (four digits, a hyphen, two digits,
  a hyphen, two digits) and a real calendar day. Otherwise: `422 invalid_request`.
- `room_id` is optional. When given, only that room's bookings are returned. If it is not
  an integer: `422 invalid_request`. If it is an integer but not one of the four rooms:
  `404 room_not_found`.

**R3. Request shape.** The body of `POST /api/bookings` must be a JSON object with all
five fields: `room_id` an integer; `date`, `start`, `end` and `booked_by` strings.
`date` follows the format in R2. `start` and `end` must each be exactly `HH:MM` with two
digits for the hour and two for the minutes, from `00:00` to `23:59`. A body that is not
valid JSON, a missing field, a field of the wrong type, or a badly formatted date or time
gives `422 invalid_request`. Fields not listed here are ignored.

**R4. Name.** `booked_by`, after removing leading and trailing whitespace, must be 1 to 40
characters long. Otherwise: `422 invalid_name`. The booking stores and returns the
trimmed name.

**R5. Times.** All of these must hold, otherwise `422 invalid_time`:
- the minutes of `start` and of `end` are `00` or `30`;
- `start` is at or after `08:00`, and `end` is at or before `22:00`;
- `start` is before `end`;
- the booking lasts at most 3 hours (180 minutes).

**R6. Room.** `room_id` must be one of the four rooms. Otherwise: `404 room_not_found`.

**R7. No overlap.** A new booking must not overlap an existing booking for the same room
on the same date. Two bookings overlap when each one starts before the other one ends.
Bookings that only touch (one ends at the time the other starts) do not overlap. Bookings
in different rooms, or on different dates, never conflict. Otherwise: `409 overlap`.

**R8. Cancel.** `DELETE /api/bookings/{id}` removes the booking and returns `204` with an
empty body. Its time is free to book again. If no booking has that id:
`404 booking_not_found`. If the id is not an integer: `422 invalid_request`.

**R9. Errors.**
- Every error response from the endpoints in section 4 has a body with exactly two
  fields: `{"error": "<code>", "message": "<text>"}`. `error` is one of the codes in
  section 6. `message` is any short text that helps a person; tests do not check it.
  This includes the `422` responses for invalid JSON, missing fields and wrong types.
- A request that fails changes nothing: no booking is created, changed or removed.
- When a `POST /api/bookings` request breaks more than one rule, only the first one in
  this order is reported: R3, R4, R5, R6, R7, R11.

**R10. The application.** `create_app` behaves as section 3 says: it serves the page,
keeps data in the one file at `db_path`, never shares data between different files, and
sees data saved earlier in the same file.

**R11. Daily limit.** One person may hold at most two bookings on the same date,
across all rooms. Two bookings belong to the same person when their `booked_by`
values are equal after removing leading and trailing whitespace and ignoring
upper and lower case. A third booking for that person on that date is rejected
with `409 daily_limit`. Cancelling a booking frees its place.

## 6. Error codes

| Status | `error` | Rule |
|---|---|---|
| 422 | `invalid_request` | R2, R3, R8 |
| 422 | `invalid_name` | R4 |
| 422 | `invalid_time` | R5 |
| 404 | `room_not_found` | R2, R6 |
| 404 | `booking_not_found` | R8 |
| 409 | `overlap` | R7 |
| 409 | `daily_limit` | R11 |

## 7. Decisions

**Already decided by the product owner.**
- P1. Dates in the past are allowed. The backend never compares a date with today.
- P2. Capacity is shown on the page only. The backend does not ask how many people come.
- P3. Anyone can cancel any booking. There is no login.
- P4. The same person may book back-to-back slots in the same room.

**Decisions made while clarifying this spec (Part 3).** A decision answers a question this
spec leaves open. It may not change sections 1 to 6 or P1 to P4: it may not reject a
request they accept, accept a request they reject, or change a route, field, status code
or error code. If you think a rule is missing, write it under "Proposed, not built" with
your reason; it is not built in this assignment.

- D1. (R3, Q9) In a POST /api/bookings body, room_id is an integer only if it is a JSON number with no decimal point and no exponent, so 1.0, 1e0, "1" and true give 422 invalid_request.
- D2. (R2, R8, Q4, Q17) In GET /api/bookings?room_id= and DELETE /api/bookings/{id}, a value is an integer if it is an optional - followed by one or more ASCII digits, so 01 and -1 are integers while +1, " 1", 1.0 and abc give 422 invalid_request; an integer that is not a room gives 404 room_not_found and one that matches no booking gives 404 booking_not_found, even when it is too large for the database.
- D3. (R2, Q5) A query parameter given with an empty value (date= or room_id=) counts as given and not valid, and gives 422 invalid_request.
- D4. (R2, Q6) GET /api/bookings checks in this order: date, then the format of room_id, then whether that room exists; only the first problem is reported.
- D5. (R2, Q7) When a query parameter appears more than once, the last value is used.
- D6. (R2, Q8) Query parameters not named in R2 are ignored, the same as unknown body fields in R3.
- D7. (R2, R3, Q2, Q3) "Digits" in dates and times means ASCII 0-9 only, and a real calendar day has a year from 0001 to 9999 in the Gregorian calendar, so year 0000 gives 422 invalid_request.
- D8. (R3, Q10) Valid JSON means RFC 8259 JSON, so NaN, Infinity and -Infinity give 422 invalid_request; when an object has a duplicate key, the last value is used.
- D9. (R3, Q11) The Content-Type header is not checked, and a body that is not valid UTF-8 counts as invalid JSON and gives 422 invalid_request.
- D10. (R4, Q12) Trimming removes the characters Python's str.strip() treats as whitespace, including Unicode spaces such as the non-breaking space; zero-width characters are not whitespace and are kept.
- D11. (R4, Q13) Name length is counted in Unicode code points after trimming.
- D12. (R4, Q14) Any characters inside the name, including tabs and newlines, are allowed and stored as typed, because R4 only limits length.
- D13. (R7, R9, Q15) The overlap check and the save happen as one step, so if two overlapping requests arrive at the same time, exactly one gets 201 and the other gets 409 overlap.
- D14. (section 2, R8, Q16) A booking id is never reused, even after that booking is cancelled.
- D15. (R9, Q19) message is a short, plain-English sentence for the person using the page, and never contains stack traces, SQL or internal names.
- D16. (sections 3 and 4, Q20) "Every body is JSON" in section 4 applies to /api/* only; /, /app.js and /styles.css are served as HTML, JavaScript and CSS.
- D17. (section 3, R10, Q21) If the database file already has any rooms, create_app does not add, change or remove rooms.
- D18. (R3) A string field that contains an unpaired surrogate (for example the JSON escape "\ud800" alone) is not valid text, so the body gives 422 invalid_request, the same as a body that is not valid UTF-8 (D9).

**Proposed, not built.**

- Daily limit (Q1). Built in Version 2 as R11 (section 5), which the product owner decided; it also settles what counts as the same person.
- Error body outside section 4 (Q18). Unknown paths, wrong methods and trailing-slash paths could return the R9 error body, but R9 covers only the endpoints in section 4, and section 6 has no error code for a 404 unknown path or a 405 wrong method; using invalid_request with those statuses would change section 6. Until the spec defines them, these responses keep FastAPI's defaults.

## 8. Change log

- Version 1: first version.
- Version 2: R11 added.
