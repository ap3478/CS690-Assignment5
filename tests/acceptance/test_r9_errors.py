"""R9. Errors: order of checks for POST /api/bookings (R3, R4, R5, R6, R7), exact
error bodies, and no change after a failed request."""

import pytest

DATE = "2031-03-14"


def existing(api):
    """Room 1, 10:00 to 12:00, so a request can also break R7."""
    return api.book(room_id=1, start="10:00", end="12:00", booked_by="First")


# Each case breaks two or more rules; the expected error is the first in R9 order.
CASES = [
    # R3 first
    ("r3_before_r4", {"room_id": "1", "booked_by": ""}, 422, "invalid_request"),
    ("r3_before_r5", {"room_id": True, "start": "07:00", "end": "07:15"}, 422, "invalid_request"),
    ("r3_before_r6", {"room_id": 9.0}, 422, "invalid_request"),
    ("r3_before_r7_bad_date", {"date": "2031-02-30", "start": "10:00", "end": "12:00"}, 422, "invalid_request"),
    ("r3_before_r7_bad_time", {"start": "9:00", "end": "11:00"}, 422, "invalid_request"),
    ("r3_time_format_before_r5", {"start": "07:00", "end": "24:00"}, 422, "invalid_request"),
    ("r3_name_type_before_r5", {"booked_by": 42, "start": "09:15", "end": "10:00"}, 422, "invalid_request"),
    ("r3_before_all", {"room_id": "9", "booked_by": " ", "start": "21:00", "end": "2:00"}, 422, "invalid_request"),
    # R4 next
    ("r4_before_r5", {"booked_by": "", "start": "07:00", "end": "08:00"}, 422, "invalid_name"),
    ("r4_before_r6", {"booked_by": "N" * 41, "room_id": 9}, 422, "invalid_name"),
    ("r4_before_r7", {"booked_by": "   ", "start": "10:00", "end": "12:00"}, 422, "invalid_name"),
    ("r4_before_r5_r6", {"booked_by": "\t", "room_id": 0, "start": "10:00", "end": "10:00"}, 422, "invalid_name"),
    # R5 next
    ("r5_before_r6", {"room_id": 9, "start": "09:15", "end": "10:00"}, 422, "invalid_time"),
    ("r5_before_r6_long", {"room_id": 5, "start": "08:00", "end": "12:00"}, 422, "invalid_time"),
    ("r5_before_r7", {"start": "09:00", "end": "12:30"}, 422, "invalid_time"),
    ("r5_before_r7_minutes", {"start": "10:15", "end": "11:00"}, 422, "invalid_time"),
]


@pytest.mark.parametrize("data,status,code", [c[1:] for c in CASES], ids=[c[0] for c in CASES])
def test_r9_post_reports_only_first_broken_rule(api, rb, data, status, code):
    existing(api)
    api.fails(lambda: api.post(rb.body(**data)), status, code, (DATE, "2031-02-28", "2031-03-01"))


def test_r9_missing_field_and_bad_name_is_invalid_request(api, rb):
    existing(api)
    data = rb.without("room_id")
    data["booked_by"] = ""
    api.fails(lambda: api.post(data), 422, "invalid_request")


def test_r9_invalid_json_with_overlap_is_invalid_request(api):
    existing(api)
    raw = '{"room_id": 1, "date": "2031-03-14", "start": "10:00", "end": "12:00", "booked_by": "Ana",}'
    api.fails(lambda: api.post_raw(raw), 422, "invalid_request")


def test_r9_failed_requests_in_a_row_change_nothing(api, rb):
    first = existing(api)
    other = api.book(room_id=2, start="08:00", end="09:00", booked_by="Other")
    attempts = [
        (lambda: api.post(rb.body(room_id="1")), 422, "invalid_request"),
        (lambda: api.post(rb.body(booked_by="")), 422, "invalid_name"),
        (lambda: api.post(rb.body(start="07:00", end="08:00")), 422, "invalid_time"),
        (lambda: api.post(rb.body(room_id=7)), 404, "room_not_found"),
        (lambda: api.post(rb.body(start="11:00", end="13:00")), 409, "overlap"),
        (lambda: api.delete(first["id"] + other["id"] + 1000), 404, "booking_not_found"),
        (lambda: api.delete("abc"), 422, "invalid_request"),
        (lambda: api.get("?date=2031-02-30"), 422, "invalid_request"),
        (lambda: api.get(f"?date={DATE}&room_id=7"), 404, "room_not_found"),
    ]
    for send, status, code in attempts:
        api.fails(send, status, code)
    assert api.bookings(DATE) == [first, other]


def test_r9_rejected_overlap_creates_nothing_in_any_room(api, rb):
    # A rejected overlap must not leave a partial booking in any room or date.
    first = existing(api)
    api.fails(lambda: api.post(rb.body(start="11:00", end="12:00")), 409, "overlap", (DATE, "2031-03-15"))
    assert api.bookings(DATE, room_id=1) == [first]
    for room in (2, 3, 4):
        assert api.bookings(DATE, room_id=room) == []
