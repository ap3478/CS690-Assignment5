"""R7. No overlap (with P4 and D13)."""

import pytest

DATE = "2031-03-14"
OTHER_DATE = "2031-03-15"


def existing(api):
    return api.book(room_id=1, start="10:00", end="12:00", booked_by="First")


@pytest.mark.parametrize(
    "start,end",
    [
        ("10:00", "12:00"),  # same times
        ("09:00", "10:30"),  # starts before, ends inside
        ("11:30", "13:00"),  # starts inside, ends after
        ("10:30", "11:30"),  # inside
        ("09:30", "12:30"),  # contains
        ("10:00", "10:30"),  # same start
        ("11:30", "12:00"),  # same end
    ],
)
def test_r7_overlapping_booking_is_overlap(api, rb, start, end):
    existing(api)
    api.fails(
        lambda: api.post(rb.body(room_id=1, start=start, end=end, booked_by="Second")),
        409,
        "overlap",
        (DATE, OTHER_DATE),
    )


def test_r7_booking_ending_when_existing_starts_is_allowed(api):
    first = existing(api)
    second = api.book(room_id=1, start="08:00", end="10:00", booked_by="Second")
    assert api.bookings(DATE) == [second, first]


def test_r7_booking_starting_when_existing_ends_is_allowed(api):
    first = existing(api)
    second = api.book(room_id=1, start="12:00", end="13:00", booked_by="Second")
    assert api.bookings(DATE) == [first, second]


def test_r7_same_person_back_to_back_is_allowed(api):
    # P4.
    first = existing(api)
    second = api.book(room_id=1, start="12:00", end="14:00", booked_by="First")
    third = api.book(room_id=1, start="08:00", end="10:00", booked_by="First")
    assert api.bookings(DATE) == [third, first, second]


def test_r7_same_time_in_another_room_is_allowed(api):
    first = existing(api)
    other = api.book(room_id=2, start="10:00", end="12:00", booked_by="Second")
    assert api.bookings(DATE) == [first, other]


def test_r7_same_time_on_another_date_is_allowed(api):
    first = existing(api)
    other = api.book(room_id=1, date=OTHER_DATE, start="10:00", end="12:00", booked_by="Second")
    assert api.bookings(DATE) == [first]
    assert api.bookings(OTHER_DATE) == [other]


def test_r7_overlap_with_one_of_several_bookings_is_overlap(api, rb):
    api.book(room_id=1, start="08:00", end="09:00")
    api.book(room_id=1, start="13:00", end="14:00")
    api.fails(lambda: api.post(rb.body(room_id=1, start="12:00", end="13:30")), 409, "overlap")
