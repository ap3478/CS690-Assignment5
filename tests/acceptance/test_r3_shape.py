"""R3. Request shape of POST /api/bookings (with decisions D1, D7, D8, D9)."""

import json

import pytest

DATE = "2031-03-14"
VALID_RAW = '{"room_id": 1, "date": "2031-03-14", "start": "09:00", "end": "10:30", "booked_by": "Ana"}'


def seed(api):
    return api.book(room_id=1, start="12:00", end="13:00", booked_by="Seed")


def test_r3_valid_body_creates_booking(api):
    seed(api)
    created = api.book(room_id=2, date=DATE, start="09:00", end="10:30", booked_by="Ana")
    assert created in api.bookings(DATE)


def test_r3_unknown_fields_are_ignored(api, rb):
    data = rb.body(extra="x", capacity=99, id=12345)
    resp = api.post(data)
    assert resp.status_code == 201
    rb.check_booking(resp.json(), rb.body())
    assert resp.json() in api.bookings(DATE)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"not json",
        b"{",
        b'{"room_id": 1,}',
        b"{'room_id': 1}",
        b"[]",
        b"null",
        b"1",
        b'"text"',
        b"[" + VALID_RAW.encode() + b"]",
    ],
)
def test_r3_body_not_a_json_object_is_invalid_request(api, raw):
    seed(api)
    api.fails(lambda: api.post_raw(raw), 422, "invalid_request")


def test_r3_nan_room_id_is_invalid_request(api):
    # D8.
    seed(api)
    raw = VALID_RAW.replace('"room_id": 1', '"room_id": NaN')
    api.fails(lambda: api.post_raw(raw), 422, "invalid_request")


@pytest.mark.parametrize("field", ["room_id", "date", "start", "end", "booked_by"])
def test_r3_missing_field_is_invalid_request(api, rb, field):
    seed(api)
    api.fails(lambda: api.post(rb.without(field)), 422, "invalid_request")


def test_r3_empty_object_is_invalid_request(api):
    seed(api)
    api.fails(lambda: api.post({}), 422, "invalid_request")


@pytest.mark.parametrize("room_id", ["1", 1.5, True, False, None, [1], {"id": 1}, ""])
def test_r3_room_id_not_an_integer_is_invalid_request(api, rb, room_id):
    # R3; D1: "1", 1.0 and true are not integers.
    seed(api)
    api.fails(lambda: api.post(rb.body(room_id=room_id)), 422, "invalid_request")


@pytest.mark.parametrize(
    "field,value",
    [
        ("date", 20310314),
        ("date", None),
        ("date", ["2031-03-14"]),
        ("start", 900),
        ("start", True),
        ("start", None),
        ("end", 1030),
        ("end", {"h": 10}),
        ("booked_by", 123),
        ("booked_by", None),
        ("booked_by", ["Ana"]),
        ("booked_by", True),
    ],
)
def test_r3_string_field_of_wrong_type_is_invalid_request(api, rb, field, value):
    seed(api)
    api.fails(lambda: api.post(rb.body(**{field: value})), 422, "invalid_request")


@pytest.mark.parametrize(
    "date",
    ["", "2031-3-14", "2031-03-4", "31-03-14", "20310314", "2031/03/14", "2031-03-14T09:00",
     " 2031-03-14", "2031-03-14 ", "2031-03-1a", "02031-03-14"],
)
def test_r3_badly_formatted_date_is_invalid_request(api, rb, date):
    # R3 uses the R2 date format; D7 ASCII digits only.
    seed(api)
    api.fails(lambda: api.post(rb.body(date=date)), 422, "invalid_request")


@pytest.mark.parametrize(
    "date", ["2031-02-30", "2031-02-29", "2031-04-31", "2031-13-01", "2031-00-10", "2031-01-00"]
)
def test_r3_impossible_date_is_invalid_request(api, rb, date):
    # R2 "real calendar day"; D7 year 0000.
    seed(api)
    api.fails(lambda: api.post(rb.body(date=date)), 422, "invalid_request", (DATE, "2031-02-28", "2031-03-01"))


def test_r3_real_leap_day_is_accepted(api):
    created = api.book(date="2032-02-29")
    assert api.bookings("2032-02-29") == [created]


BAD_TIMES = ["", "9:00", "09:0", "0900", "09:00:00", "09.00", "09-00", "24:00", "23:60", "99:99",
             "ab:cd", " 09:00", "09:00 ", "-1:00", "+9:00", "9:000"]


@pytest.mark.parametrize("start", BAD_TIMES)
def test_r3_badly_formatted_start_is_invalid_request(api, rb, start):
    seed(api)
    api.fails(lambda: api.post(rb.body(start=start, end="10:30")), 422, "invalid_request")


@pytest.mark.parametrize("end", BAD_TIMES)
def test_r3_badly_formatted_end_is_invalid_request(api, rb, end):
    seed(api)
    api.fails(lambda: api.post(rb.body(start="09:00", end=end)), 422, "invalid_request")
