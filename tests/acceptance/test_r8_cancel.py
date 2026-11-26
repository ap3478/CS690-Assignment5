"""R8. Cancel (with P3, D2, D14)."""

import pytest

DATE = "2031-03-14"


def test_r8_cancel_returns_204_with_empty_body(api):
    booking = api.book()
    resp = api.delete(booking["id"])
    assert resp.status_code == 204
    assert resp.content == b""


def test_r8_cancel_removes_only_that_booking(api):
    keep = api.book(room_id=1, start="08:00", end="09:00")
    gone = api.book(room_id=1, start="09:00", end="10:00")
    other_day = api.book(room_id=1, date="2031-03-15", start="09:00", end="10:00")
    assert api.delete(gone["id"]).status_code == 204
    assert api.bookings(DATE) == [keep]
    assert api.bookings("2031-03-15") == [other_day]


def test_r8_cancelled_time_can_be_booked_again(api):
    first = api.book(room_id=2, start="10:00", end="12:00", booked_by="First")
    assert api.delete(first["id"]).status_code == 204
    again = api.book(room_id=2, start="10:00", end="12:00", booked_by="Someone else")
    assert api.bookings(DATE) == [again]


def test_r8_unknown_id_is_booking_not_found(api):
    booking = api.book()
    unknown = booking["id"] + 1000
    api.fails(lambda: api.delete(unknown), 404, "booking_not_found")


def test_r8_cancel_twice_is_booking_not_found(api):
    booking = api.book()
    keep = api.book(start="12:00", end="13:00")
    assert api.delete(booking["id"]).status_code == 204
    api.fails(lambda: api.delete(booking["id"]), 404, "booking_not_found")
    assert api.bookings(DATE) == [keep]


@pytest.mark.parametrize("booking_id", ["0", "-1"])
def test_r8_integer_matching_no_booking_is_booking_not_found(api, booking_id):
    # D2: -1 and values too large for the database are integers.
    booking = api.book()
    if int(booking_id) == booking["id"]:
        pytest.skip("the spec does not fix id values; this id happens to exist")
    api.fails(lambda: api.delete(booking_id), 404, "booking_not_found")


@pytest.mark.parametrize("booking_id", ["abc", "1.0", "1e0", "true"])
def test_r8_id_not_an_integer_is_invalid_request(api, booking_id):
    # R8; D2: +1, " 1", 1.0, abc are not integers.
    api.book()
    api.fails(lambda: api.delete(booking_id), 422, "invalid_request")
