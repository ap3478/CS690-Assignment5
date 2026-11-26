I checked the page, the spec and the backend against each other and changed nothing. Only one item disagrees. The page has a special message for a 404 from `GET /api/rooms`, and the spec defines no error for that endpoint. Everything else matches on all three sides, including R11 and `daily_limit`.

| # | Item | What the page does | What the spec says | What the backend does | Match or mismatch |
|---|---|---|---|---|---|
| 1 | `GET /api/rooms` request | `app.js:161`, no query or body | §4: `200`, a list of rooms (R1) | `routes.py:37-40` | Match |
| 2 | Room fields read | `room.id`, `room.name`, `room.capacity` (`app.js:111,114,119,173-174`) | §4: exactly `id`, `name`, `capacity`; R1 ordered by id | `models.py:14-16`; `repository.py:75` `ORDER BY id` | Match |
| 3 | 404 on `GET /api/rooms` | `app.js:163-164` shows "The backend is not built yet." | R1 and §6 define no error for this endpoint | Route always exists and never sends 404 (`routes.py:37`) | Mismatch: not in the spec |
| 4 | `GET /api/bookings?date=` request | `app.js:148`, `date` = the `<input type="date">` value (string, may be `""` if the user clears it) | R2: `date` required, `YYYY-MM-DD`, real day, else `422 invalid_request`; D3: an empty value gives 422; D7 | `service.py:151-152`, `routes.py:42-49` | Match |
| 5 | `room_id` query param | Never sent | R2, D2, D4: optional | Built (`service.py:154-160`) | Match (the page does not use it) |
| 6 | Booking fields read from GET | `id`, `room_id` (compared with `===` to `room.id`, so it must be an integer), `start`, `end`, `booked_by` (`app.js:119,129,134-135`) | §4: six fields, `room_id` integer; R2 ordered by room_id, start | `models.py:28-37`; `repository.py:85` | Match |
| 7 | `POST /api/bookings` body | `app.js:183-189`: `room_id` = `Number(...)` of a room id (integer), `date` string, `start`/`end` strings from 08:00-21:30 / 08:30-22:00 in 30-minute steps, `booked_by` raw untrimmed string; `Content-Type: application/json` | §4 body; R3; D1; D9 (Content-Type not checked) | `service.py:165-192`; `routes.py:51-58` reads raw bytes | Match |
| 8 | POST success | Expects 2xx, reads `booking.start`, `booking.end`, `booking.booked_by` (`app.js:192`) | `201`, the new booking; R4 returns the trimmed name | `routes.py:58` 201; `service.py:195,216` trims | Match |
| 9 | `DELETE /api/bookings/{id}` | `app.js:203`, id = `booking.id` (integer); 204 means no body (`app.js:42-44`) | R8: `204` with an empty body; D2; D14 | `routes.py:60-66`; `service.py:226-232` | Match |
| 10 | Error body shape | Reads `data.error` and `data.message` as strings (`app.js:52-53`); falls back if the body is not JSON | R9: exactly `{"error","message"}` | `routes.py:19-21`; FastAPI 422s rewritten (`main.py:30-36`) | Match |
| 11 | `invalid_request` 422 | MESSAGES (`app.js:16`), and also shows the server `message` (`app.js:62-63`) | §6: R2, R3, R8; D15 plain-English message | `service.py:37,46` | Match |
| 12 | `invalid_name` 422 | `app.js:17` "40 characters at most" (the HTML has `maxlength="60"`, so the backend enforces the limit) | R4: 1-40 chars after trimming | `service.py:195-197` | Match |
| 13 | `invalid_time` 422 | `app.js:18`: half-hours, 08:00-22:00, at most 3 h | R5 | `service.py:200-209` | Match |
| 14 | `room_not_found` 404 | `app.js:19` | §6: R2, R6 | `service.py:158-159,212-213` | Match |
| 15 | `booking_not_found` 404 | `app.js:20` | §6: R8 | `service.py:231-232` | Match |
| 16 | `overlap` 409 | `app.js:21` | R7; D13 atomic | `repository.py:109-119` (inside `BEGIN IMMEDIATE`) | Match |
| 17 | `daily_limit` 409 | `app.js:22` "You already have 2 bookings on that day" | R11: at most 2 per person per date across all rooms, trimmed and case-folded (D19); checked after R7 (R9 order) | `service.py:32,91-93,217-221`; `repository.py:120-127` checks after overlap, in the same lock | Match |
| 18 | Unknown code or status | Generic "The server answered N..." (`app.js:68`) | Q18: unknown paths and wrong methods keep FastAPI defaults; no other codes exist | No codes outside §6 (`service.py:45-53`) | Match (this is only a fallback) |
| 19 | Page files | `index.html:8,47` loads `styles.css` and `app.js` (relative to `/`) | §3, D16: `/`, `/app.js`, `/styles.css` as HTML, JS, CSS | `main.py:41-51` with the right media types | Match |

**Mismatches**
- #3: The page differs. `frontend/app.js:163-164` handles a `404` from `GET /api/rooms`, which the spec does not define (R1 and §6 have no error for that endpoint). The spec and the backend (`app/routes.py:37-40`) agree, so nothing needs changing in the backend. The page's branch only runs when the route is missing, and the page belongs to the other team.

**Observation (not a mismatch):** for `invalid_request` the page shows its own sentence followed by the server's `message`. With the backend's current text (`app/service.py:37`), the user sees "The request was not valid. The request is not valid. Check the date, times, room and name." The spec allows any short `message`, so this follows the contract but repeats itself on screen.

Files: `/Users/ga/cs690/cs690-assignment5/frontend/app.js`, `/Users/ga/cs690/cs690-assignment5/frontend/index.html`, `/Users/ga/cs690/cs690-assignment5/docs/spec.md`, `/Users/ga/cs690/cs690-assignment5/app/routes.py`, `/Users/ga/cs690/cs690-assignment5/app/main.py`, `/Users/ga/cs690/cs690-assignment5/app/service.py`, `/Users/ga/cs690/cs690-assignment5/app/repository.py`, `/Users/ga/cs690/cs690-assignment5/app/models.py`
