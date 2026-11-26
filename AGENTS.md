# AGENTS.md

## Project

RoomBook, a study-room booking app. The page in `frontend/` is finished and belongs to
another team. The backend in `app/` is built to match `docs/spec.md`.

## General rules

- Read `docs/spec.md` before every change. The spec is the source of truth: when code
  and spec disagree, the spec wins. When the spec is unclear, stop and ask. Do not guess.
- Never edit anything in `frontend/`.
- Never change a test in `tests/acceptance/` to make code pass.
- Do only the task you were given. Do not add endpoints, fields, error codes, rules,
  packages or features that the spec does not ask for.
- Python 3.11 or later. Use only the packages in `requirements.txt`.
- Run the tests with `python -m pytest`.

## Backend rules

-Layers: `app/routes.py` handles HTTP only (parse the request, call the service,
  turn results and errors into responses). `app/service.py` enforces every rule in
  spec section 5. `app/repository.py` is the only file that contains SQL or imports
  `sqlite3`. `app/models.py` holds the request and booking shapes. Routes call the
  service, never the repository.
- `app/main.py` defines `create_app(db_path: str = "roombook.db")` exactly as spec
  section 3 says: create tables and seed the four rooms if missing, serve
  `frontend/index.html`, `/app.js` and `/styles.css`, and keep all data in `db_path`.
- Every error response, including FastAPI's own 422s, 404s and 405s, has exactly the
  body `{"error": "<code>", "message": "<text>"}` from R9, with a code from section 6.
- Use `sqlite3` from the standard library. No ORM, no new packages.
- Open a new connection for each repository call and close it when done. Never share
  one connection between requests: FastAPI runs requests on several threads.
- Validate `POST /api/bookings` by hand in the service, in R9 order (R3, R4, R5, R6,
  R7), and report only the first rule broken. Do not rely on FastAPI/Pydantic
  validation for this: its order differs and it coerces types.
- Never coerce types: for `room_id`, `"1"`, `1.0` and `true` are not integers.
- A failed request changes nothing in the database.
- After every task, run `python tools/check_layers.py` and `python -m pytest`, and
  report both results.
