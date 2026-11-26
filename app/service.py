"""The rules of RoomBook (spec section 5, with decisions D1 to D17).

Every check is done here by hand. Nothing is saved until every check has passed, so
a request that fails changes nothing (R9).
"""

from __future__ import annotations

import datetime
import json
import re

from app.models import Booking, BookingRequest, Room
from app.repository import Repository

# Formats (R2, R3; D2, D7). re.fullmatch, so a trailing newline never matches.
DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
TIME_RE = re.compile(r"[0-9]{2}:[0-9]{2}")
INT_RE = re.compile(r"-?[0-9]+")

# Range of an SQLite integer. An integer outside it can match no booking id.
INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1

# R4 and R5.
NAME_MAX = 40
OPEN_MINUTE = 8 * 60
CLOSE_MINUTE = 22 * 60
MAX_LENGTH_MINUTES = 180

FIELDS = ("room_id", "date", "start", "end", "booked_by")

MESSAGES = {
    "invalid_request": "The request is not valid. Check the date, times, room and name.",
    "invalid_name": "Please enter a name of 1 to 40 characters.",
    "invalid_time": "Bookings run in 30-minute steps between 08:00 and 22:00, for up to 3 hours.",
    "room_not_found": "That room does not exist.",
    "booking_not_found": "That booking does not exist. It may already be cancelled.",
    "overlap": "That room is already booked for part of that time.",
}
STATUS = {
    "invalid_request": 422,
    "invalid_name": 422,
    "invalid_time": 422,
    "room_not_found": 404,
    "booking_not_found": 404,
    "overlap": 409,
}


class ServiceError(Exception):
    """A broken rule: an HTTP status, an error code from section 6, and a message."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code
        self.status = STATUS[code]
        self.message = MESSAGES[code]


class _LongInteger:
    """A JSON integer with too many digits to convert safely. It is still an integer
    (D1), so R3 accepts it, and it can never be a room (R6)."""


def _parse_json_int(text: str) -> int | _LongInteger:
    if len(text.lstrip("-")) > 30:
        return _LongInteger()
    return int(text)


def _reject_constant(name: str) -> None:
    # D8: NaN, Infinity and -Infinity are not RFC 8259 JSON.
    raise ValueError(f"not JSON: {name}")


def _is_valid_text(value: str) -> bool:
    """D18: False if the string holds an unpaired surrogate, which UTF-8 cannot encode."""
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _is_date(value: str) -> bool:
    """R2 format and a real calendar day, years 0001 to 9999 (D7)."""
    if not DATE_RE.fullmatch(value):
        return False
    try:
        datetime.date(int(value[0:4]), int(value[5:7]), int(value[8:10]))
    except ValueError:
        return False
    return True


def _is_time(value: str) -> bool:
    """R3: exactly HH:MM from 00:00 to 23:59."""
    return bool(TIME_RE.fullmatch(value)) and int(value[0:2]) <= 23 and int(value[3:5]) <= 59


def _minutes(value: str) -> int:
    return int(value[0:2]) * 60 + int(value[3:5])


def _int_in_int64(value: str) -> int | None:
    """Value already matches INT_RE (D2). Its int, or None if outside the SQLite range.

    Long digit strings are measured before int() so huge values are never converted.
    """
    digits = value.lstrip("-").lstrip("0")
    if len(digits) > 19:
        return None
    number = int(value)
    if number < INT64_MIN or number > INT64_MAX:
        return None
    return number


class BookingService:
    """Enforces R1 to R9. Talks to storage only through the repository."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def _room_ids(self) -> set[int]:
        return {row["id"] for row in self.repo.list_rooms()}

    # R1 ------------------------------------------------------------------------------

    def list_rooms(self) -> list[Room]:
        return [Room(row["id"], row["name"], row["capacity"]) for row in self.repo.list_rooms()]

    # R2 ------------------------------------------------------------------------------

    def list_bookings(self, date_raw: str | None, room_id_raw: str | None) -> list[Booking]:
        """date_raw and room_id_raw are the last values given (D5), or None if absent.

        Checks in D4 order: date, room_id format, room exists.
        """
        if date_raw is None or not _is_date(date_raw):
            raise ServiceError("invalid_request")
        room_id: int | None = None
        if room_id_raw is not None:
            if not INT_RE.fullmatch(room_id_raw):
                raise ServiceError("invalid_request")
            candidate = _int_in_int64(room_id_raw)
            if candidate is None or candidate not in self._room_ids():
                raise ServiceError("room_not_found")
            room_id = candidate
        return [Booking(**row) for row in self.repo.list_bookings(date_raw, room_id)]

    # R3 to R7 ------------------------------------------------------------------------

    def create_booking(self, raw_body: bytes) -> Booking:
        """Validate a POST /api/bookings body in R9 order (R3, R4, R5, R6, R7) and save it.

        Only the first broken rule is reported.
        """
        # R3: valid UTF-8 (D9), RFC 8259 JSON (D8), an object with the five fields.
        try:
            data = json.loads(
                raw_body.decode("utf-8"),
                parse_int=_parse_json_int,
                parse_constant=_reject_constant,
            )
        except (UnicodeDecodeError, ValueError, RecursionError):
            raise ServiceError("invalid_request") from None
        if not isinstance(data, dict) or any(field not in data for field in FIELDS):
            raise ServiceError("invalid_request")
        room_id = data["room_id"]
        date, start, end, booked_by = data["date"], data["start"], data["end"], data["booked_by"]
        # D1: an integer is a JSON number with no decimal point or exponent; bool is not.
        if type(room_id) is not int and not isinstance(room_id, _LongInteger):
            raise ServiceError("invalid_request")
        if any(type(v) is not str for v in (date, start, end, booked_by)):
            raise ServiceError("invalid_request")
        # D18: a string with an unpaired surrogate (e.g. "\ud800") is not valid text.
        if not all(_is_valid_text(v) for v in (date, start, end, booked_by)):
            raise ServiceError("invalid_request")
        if not _is_date(date) or not _is_time(start) or not _is_time(end):
            raise ServiceError("invalid_request")

        # R4: trimmed name of 1 to 40 code points (D10 to D12).
        name = booked_by.strip()
        if not 1 <= len(name) <= NAME_MAX:
            raise ServiceError("invalid_name")

        # R5: 30-minute steps, inside opening hours, start before end, at most 3 hours.
        start_min, end_min = _minutes(start), _minutes(end)
        if (
            start[3:5] not in ("00", "30")
            or end[3:5] not in ("00", "30")
            or start_min < OPEN_MINUTE
            or end_min > CLOSE_MINUTE
            or start_min >= end_min
            or end_min - start_min > MAX_LENGTH_MINUTES
        ):
            raise ServiceError("invalid_time")

        # R6: one of the rooms. The number is compared here, never sent to SQLite.
        if isinstance(room_id, _LongInteger) or room_id not in self._room_ids():
            raise ServiceError("room_not_found")

        # R7: overlap check and save in one step (D13).
        request = BookingRequest(room_id, date, start, end, name)
        row = self.repo.create_booking_if_free(**request.to_dict())
        if row is None:
            raise ServiceError("overlap")
        return Booking(**row)

    # R8 ------------------------------------------------------------------------------

    def cancel_booking(self, id_raw: str) -> None:
        """Remove the booking with that id (D2 format)."""
        if not INT_RE.fullmatch(id_raw):
            raise ServiceError("invalid_request")
        booking_id = _int_in_int64(id_raw)
        if booking_id is None or not self.repo.delete_booking(booking_id):
            raise ServiceError("booking_not_found")
