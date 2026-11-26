"""Characterization tests for legacy/old_format.py (Part 10).

Every expected value below comes from running the current code, right or wrong. They
pin what it does today, so a refactor that changes any behavior fails a test. Values
marked "BUG: pinned, not fixed" are wrong, and stay pinned until a separate change
fixes them on purpose.
"""

import pytest

from legacy.old_format import ROOMS, parse_old_row, to_24h


def row(**overrides):
    data = {"room": "Room A", "day": "3/14/2031", "from": "9:00 AM", "to": "10:30 AM", "who": "ana"}
    data.update(overrides)
    return data


# ---------------------------------------------------------------- to_24h

def test_legacy_to_24h_morning_is_zero_padded():
    assert to_24h("9:00 AM") == "09:00"


def test_legacy_to_24h_afternoon_adds_twelve():
    assert to_24h("1:00 PM") == "13:00"
    assert to_24h("11:30 PM") == "23:30"


def test_legacy_to_24h_without_am_pm_keeps_the_hour():
    assert to_24h("8:30") == "08:30"


def test_legacy_to_24h_strips_outer_whitespace():
    assert to_24h("  7:30 AM  ") == "07:30"


def test_legacy_to_24h_extra_seconds_are_dropped():
    assert to_24h("9:00:15 AM") == "09:00"


# BUG: pinned, not fixed
def test_legacy_to_24h_noon_becomes_24():
    assert to_24h("12:15 PM") == "24:15"
    assert to_24h("12:30 PM") == "24:30"


# BUG: pinned, not fixed
def test_legacy_to_24h_midnight_am_stays_12():
    assert to_24h("12:00 AM") == "12:00"


# BUG: pinned, not fixed
def test_legacy_to_24h_hour_past_12_pm_goes_past_24():
    assert to_24h("13:00 PM") == "25:00"


# BUG: pinned, not fixed
def test_legacy_to_24h_lowercase_pm_is_ignored():
    assert to_24h("3:00 pm") == "03:00"


# BUG: pinned, not fixed
def test_legacy_to_24h_single_digit_minutes_are_not_padded():
    assert to_24h("9:5 AM") == "09:5"


# BUG: pinned, not fixed
def test_legacy_to_24h_two_spaces_before_pm_lose_the_pm():
    assert to_24h("9:00  PM") == "09:00"


# BUG: pinned, not fixed
def test_legacy_to_24h_zero_hour_pm_becomes_12():
    assert to_24h("0:00 PM") == "12:00"


def test_legacy_to_24h_without_colon_raises_index_error():
    with pytest.raises(IndexError):
        to_24h("9 AM")


@pytest.mark.parametrize("text", ["x:00 AM", "", "   "])
def test_legacy_to_24h_non_numeric_hour_raises_value_error(text):
    with pytest.raises(ValueError):
        to_24h(text)


# ---------------------------------------------------------------- parse_old_row

def test_legacy_parse_old_row_normal_row():
    assert parse_old_row(row()) == {
        "room_id": 1,
        "date": "2031-03-14",
        "start": "09:00",
        "end": "10:30",
        "booked_by": "Ana",
    }


def test_legacy_parse_old_row_sample_rows():
    # The rows of legacy/old_bookings.csv, as the code converts them today.
    assert parse_old_row(row(room="Room B", day="3/14/2031", **{"from": "1:00 PM", "to": "2:00 PM"}, who="  bo chen")) == {
        "room_id": 2, "date": "2031-03-14", "start": "13:00", "end": "14:00", "booked_by": "Bo chen"}
    assert parse_old_row(row(room="Room C", day="12/1/31", **{"from": "10:00 AM", "to": "11:30 AM"}, who="Priya")) == {
        "room_id": 3, "date": "2031-12-01", "start": "10:00", "end": "11:30", "booked_by": "Priya"}
    assert parse_old_row(row(room="Room D", day="03/02/2031", **{"from": "8:30", "to": "10:00"}, who="lee")) == {
        "room_id": 4, "date": "2031-03-02", "start": "08:30", "end": "10:00", "booked_by": "Lee"}


def test_legacy_rooms_table():
    assert ROOMS == {"Room A": 1, "Room B": 2, "Room C": 3, "Room D": 4}


def test_legacy_parse_old_row_room_is_stripped():
    assert parse_old_row(row(room="  Room B "))["room_id"] == 2


def test_legacy_parse_old_row_two_digit_year_gets_20():
    assert parse_old_row(row(day="12/1/31"))["date"] == "2031-12-01"


def test_legacy_parse_old_row_month_and_day_are_zero_padded():
    assert parse_old_row(row(day="3/4/2031"))["date"] == "2031-03-04"
    assert parse_old_row(row(day=" 03/02/2031 "))["date"] == "2031-03-02"


# BUG: pinned, not fixed
def test_legacy_parse_old_row_three_digit_year_is_kept_as_is():
    assert parse_old_row(row(day="3/14/131"))["date"] == "131-03-14"


# BUG: pinned, not fixed
def test_legacy_parse_old_row_extra_date_part_is_ignored():
    assert parse_old_row(row(day="3/14/2031/9"))["date"] == "2031-03-14"


def test_legacy_parse_old_row_name_is_stripped_and_first_letter_upper():
    assert parse_old_row(row(who="  bo chen "))["booked_by"] == "Bo chen"


# BUG: pinned, not fixed
def test_legacy_parse_old_row_only_first_letter_changes_case():
    assert parse_old_row(row(who="mcDonald"))["booked_by"] == "McDonald"
    assert parse_old_row(row(who="ANA"))["booked_by"] == "ANA"


def test_legacy_parse_old_row_times_use_to_24h():
    result = parse_old_row(row(**{"from": "12:30 PM", "to": "3:00 pm"}))
    assert (result["start"], result["end"]) == ("24:30", "03:00")


def test_legacy_parse_old_row_unknown_room_raises_key_error():
    with pytest.raises(KeyError):
        parse_old_row(row(room="Room E"))


def test_legacy_parse_old_row_room_name_is_case_sensitive():
    with pytest.raises(KeyError):
        parse_old_row(row(room="room a"))


@pytest.mark.parametrize("day", ["2031-03-14", "3/14", "3"])
def test_legacy_parse_old_row_day_without_three_parts_raises_index_error(day):
    with pytest.raises(IndexError):
        parse_old_row(row(day=day))


def test_legacy_parse_old_row_empty_name_raises_index_error():
    with pytest.raises(IndexError):
        parse_old_row(row(who="   "))


def test_legacy_parse_old_row_missing_column_raises_key_error():
    data = row()
    del data["who"]
    with pytest.raises(KeyError):
        parse_old_row(data)


def test_legacy_parse_old_row_bad_time_raises_value_error():
    with pytest.raises(ValueError):
        parse_old_row(row(**{"from": "noon"}))
