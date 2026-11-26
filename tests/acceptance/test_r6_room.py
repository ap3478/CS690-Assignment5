"""R6. Room."""

import pytest

DATE = "2031-03-14"


@pytest.mark.parametrize("room_id", [1, 2, 3, 4])
def test_r6_each_of_the_four_rooms_can_be_booked(api, room_id):
    created = api.book(room_id=room_id)
    assert api.bookings(DATE, room_id=room_id) == [created]


@pytest.mark.parametrize("room_id", [0, 5, -1, 99])
def test_r6_unknown_room_is_room_not_found(api, rb, room_id):
    # R6; D1: any JSON number without decimal point or exponent is an integer.
    api.book(room_id=1, start="12:00", end="13:00", booked_by="Seed")
    api.fails(lambda: api.post(rb.body(room_id=room_id)), 404, "room_not_found")
