"""R2. List bookings (with decisions D2 to D7)."""

import pytest

DATE = "2031-03-14"
OTHER_DATE = "2031-03-15"


def seed(api):
    """Bookings created out of order, on DATE and on another date."""
    made = [
        api.book(room_id=3, start="10:00", end="11:00", booked_by="Cy"),
        api.book(room_id=1, start="14:00", end="15:00", booked_by="Bo"),
        api.book(room_id=2, start="09:00", end="10:00", booked_by="Di"),
        api.book(room_id=1, start="08:00", end="09:30", booked_by="Ana"),
        api.book(room_id=1, date=OTHER_DATE, start="11:00", end="12:00", booked_by="Ed"),
    ]
    return made


def test_r2_date_with_no_bookings_gives_empty_list(api):
    assert api.bookings(DATE) == []


def test_r2_lists_date_ordered_by_room_then_start(api):
    cy, bo, di, ana, _ed = seed(api)
    assert api.bookings(DATE) == [ana, bo, di, cy]


def test_r2_other_dates_are_not_listed(api):
    *_rest, ed = seed(api)
    assert api.bookings(OTHER_DATE) == [ed]


def test_r2_room_filter_returns_only_that_room_ordered_by_start(api):
    _cy, bo, _di, ana, _ed = seed(api)
    assert api.bookings(DATE, room_id=1) == [ana, bo]


def test_r2_room_filter_with_no_bookings_gives_empty_list(api):
    seed(api)
    assert api.bookings(DATE, room_id=4) == []


@pytest.mark.parametrize("date", ["2031-02-28", "2032-02-29", "0001-01-01", "9999-12-31", "2020-01-01"])
def test_r2_real_calendar_days_are_accepted(api, date):
    # R2 format and real day; D7 years 0001 to 9999; P1 past dates allowed.
    assert api.bookings(date) == []


def test_r2_missing_date_is_invalid_request(api):
    seed(api)
    api.fails(lambda: api.get(""), 422, "invalid_request", (DATE, OTHER_DATE))


def test_r2_missing_date_with_room_id_is_invalid_request(api):
    seed(api)
    api.fails(lambda: api.get("?room_id=1"), 422, "invalid_request", (DATE, OTHER_DATE))


@pytest.mark.parametrize(
    "date",
    [
        "",  # D3
        "2031-3-14",
        "2031-03-4",
        "31-03-14",
        "20310314",
        "2031/03/14",
        "2031-03-14T00:00",
        "%202031-03-14",
        "2031-03-14%20",
        "2031-03-1a",
        "abcd-ef-gh",
        "02031-03-14",
    ],
)
def test_r2_badly_formatted_date_is_invalid_request(api, date):
    seed(api)
    api.fails(lambda: api.get(f"?date={date}"), 422, "invalid_request", (DATE, OTHER_DATE))


@pytest.mark.parametrize(
    "date",
    ["2031-02-30", "2031-02-29", "2031-04-31", "2031-13-01", "2031-00-10", "2031-01-00", "2031-01-32"],
)
def test_r2_impossible_date_is_invalid_request(api, date):
    seed(api)
    api.fails(lambda: api.get(f"?date={date}"), 422, "invalid_request", (DATE, OTHER_DATE))


@pytest.mark.parametrize("room_id", ["abc", "1.0", "1e0", "true", "one"])
def test_r2_room_id_not_an_integer_is_invalid_request(api, room_id):
    # R2; D2 (+1, " 1", 1.0, abc are not integers); D3 (empty value).
    seed(api)
    api.fails(
        lambda: api.get(f"?date={DATE}&room_id={room_id}"), 422, "invalid_request", (DATE, OTHER_DATE)
    )


@pytest.mark.parametrize("room_id", ["0", "5", "-1"])
def test_r2_unknown_room_is_room_not_found(api, room_id):
    # R2; D2 (-1 and very large values are integers).
    seed(api)
    api.fails(
        lambda: api.get(f"?date={DATE}&room_id={room_id}"), 404, "room_not_found", (DATE, OTHER_DATE)
    )


def test_r2_unknown_query_parameters_are_ignored(api):
    # D6.
    cy, bo, di, ana, _ed = seed(api)
    resp = api.get(f"?date={DATE}&foo=bar&limit=1")
    assert resp.status_code == 200
    assert resp.json() == [ana, bo, di, cy]
