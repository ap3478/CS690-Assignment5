"""R11. Daily limit: at most two bookings per person per date, across all rooms.

Same person: booked_by equal after trimming leading and trailing whitespace and
ignoring upper and lower case. A third booking gives 409 daily_limit. Cancelling a
booking frees its place. In R9 order, R11 is checked last, after R7.
"""

DATE = "2031-03-14"
OTHER_DATE = "2031-03-15"


def two_for_ana(api):
    """Two bookings for Ana on DATE, in different rooms."""
    first = api.book(room_id=1, start="09:00", end="10:00", booked_by="Ana")
    second = api.book(room_id=2, start="11:00", end="12:00", booked_by="Ana")
    return first, second


def test_r11_third_booking_on_same_date_is_daily_limit(api, rb):
    two_for_ana(api)
    api.fails(
        lambda: api.post(rb.body(room_id=3, start="13:00", end="14:00", booked_by="Ana")),
        409,
        "daily_limit",
        (DATE, OTHER_DATE),
    )


def test_r11_case_and_outer_spaces_are_the_same_person(api, rb):
    api.book(room_id=1, start="09:00", end="10:00", booked_by="Ana")
    api.book(room_id=2, start="11:00", end="12:00", booked_by="  aNA ")
    api.fails(
        lambda: api.post(rb.body(room_id=3, start="13:00", end="14:00", booked_by=" ANA\t")),
        409,
        "daily_limit",
        (DATE,),
    )


def test_r11_cancelling_one_of_two_allows_a_new_one(api):
    first, second = two_for_ana(api)
    assert api.delete(first["id"]).status_code == 204
    third = api.book(room_id=3, start="13:00", end="14:00", booked_by="Ana")
    assert api.bookings(DATE) == [second, third]


def test_r11_another_date_is_allowed(api):
    two_for_ana(api)
    other = api.book(room_id=1, date=OTHER_DATE, start="09:00", end="10:00", booked_by="Ana")
    assert api.bookings(OTHER_DATE) == [other]


def test_r11_another_person_is_allowed(api):
    first, second = two_for_ana(api)
    bo = api.book(room_id=3, start="13:00", end="14:00", booked_by="Bo")
    assert api.bookings(DATE) == [first, second, bo]


def test_r11_inner_spaces_make_a_different_person(api):
    # Only leading and trailing whitespace is removed; inner spaces still count.
    api.book(room_id=1, start="09:00", end="10:00", booked_by="Ana Lopez")
    api.book(room_id=2, start="11:00", end="12:00", booked_by="Ana Lopez")
    other = api.book(room_id=3, start="13:00", end="14:00", booked_by="Ana  Lopez")
    assert other in api.bookings(DATE)


def test_r11_overlap_is_reported_before_daily_limit(api, rb):
    # R9 order: R7 before R11.
    two_for_ana(api)
    api.fails(
        lambda: api.post(rb.body(room_id=1, start="09:30", end="10:30", booked_by="Ana")),
        409,
        "overlap",
        (DATE,),
    )


def test_r11_time_rule_is_reported_before_daily_limit(api, rb):
    # R9 order: R5 before R11.
    two_for_ana(api)
    api.fails(
        lambda: api.post(rb.body(room_id=3, start="13:15", end="14:00", booked_by="Ana")),
        422,
        "invalid_time",
        (DATE,),
    )
