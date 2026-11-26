"""R5. Times."""

import pytest

DATE = "2031-03-14"


def seed(api):
    return api.book(room_id=2, start="12:00", end="13:00", booked_by="Seed")


@pytest.mark.parametrize(
    "start,end",
    [
        ("08:00", "11:00"),  # earliest start, exactly 3 hours
        ("19:00", "22:00"),  # latest end, exactly 3 hours
        ("21:30", "22:00"),  # 30 minutes ending at 22:00
        ("08:00", "08:30"),  # 30 minutes starting at 08:00
        ("09:30", "10:30"),  # minutes 30
        ("10:00", "12:30"),  # 2h30
        ("13:30", "16:30"),  # exactly 3 hours on half hours
    ],
)
def test_r5_valid_times_are_accepted(api, start, end):
    created = api.book(room_id=1, start=start, end=end)
    assert api.bookings(DATE, room_id=1) == [created]


@pytest.mark.parametrize(
    "start,end",
    [
        ("07:30", "09:00"),  # start before 08:00
        ("07:00", "08:00"),  # ends exactly at opening
        ("00:00", "01:00"),
        ("21:00", "22:30"),  # end after 22:00
        ("22:00", "23:00"),  # starts at closing
        ("22:30", "23:30"),
        ("23:00", "23:30"),
    ],
)
def test_r5_outside_opening_hours_is_invalid_time(api, rb, start, end):
    seed(api)
    api.fails(lambda: api.post(rb.body(start=start, end=end)), 422, "invalid_time")


@pytest.mark.parametrize("start,end", [("10:00", "10:00"), ("08:00", "08:00"), ("22:00", "22:00")])
def test_r5_start_equal_to_end_is_invalid_time(api, rb, start, end):
    seed(api)
    api.fails(lambda: api.post(rb.body(start=start, end=end)), 422, "invalid_time")


@pytest.mark.parametrize("start,end", [("11:00", "10:00"), ("10:30", "10:00"), ("21:00", "08:00")])
def test_r5_start_after_end_is_invalid_time(api, rb, start, end):
    seed(api)
    api.fails(lambda: api.post(rb.body(start=start, end=end)), 422, "invalid_time")


@pytest.mark.parametrize("start,end", [("08:00", "11:30"), ("09:00", "13:00"), ("08:00", "22:00"), ("18:30", "22:00")])
def test_r5_longer_than_three_hours_is_invalid_time(api, rb, start, end):
    seed(api)
    api.fails(lambda: api.post(rb.body(start=start, end=end)), 422, "invalid_time")


@pytest.mark.parametrize(
    "start,end",
    [
        ("09:15", "10:00"),
        ("09:00", "10:15"),
        ("09:45", "10:30"),
        ("09:00", "09:45"),
        ("09:01", "10:00"),
        ("09:00", "10:59"),
        ("09:10", "10:10"),
    ],
)
def test_r5_minutes_not_00_or_30_is_invalid_time(api, rb, start, end):
    seed(api)
    api.fails(lambda: api.post(rb.body(start=start, end=end)), 422, "invalid_time")
