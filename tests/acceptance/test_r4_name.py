"""R4. Name (with decisions D10, D11, D12)."""

import pytest

DATE = "2031-03-14"


def seed(api):
    return api.book(room_id=1, start="12:00", end="13:00", booked_by="Seed")


def stored_name(api, booked_by):
    created = api.book(booked_by=booked_by)
    listed = [b for b in api.bookings(DATE) if b["id"] == created["id"]]
    assert listed == [created]
    return created["booked_by"]


def test_r4_one_character_name_is_accepted(api):
    assert stored_name(api, "A") == "A"


def test_r4_forty_character_name_is_accepted(api):
    name = "N" * 40
    assert stored_name(api, name) == name


def test_r4_forty_characters_after_trimming_is_accepted(api):
    name = "x" * 40
    assert stored_name(api, "   " + name + "\t ") == name


def test_r4_name_is_trimmed_when_stored_and_returned(api):
    assert stored_name(api, "  Ana Lopez \n") == "Ana Lopez"


def test_r4_unicode_spaces_are_trimmed(api):
    # D10: str.strip() whitespace includes the non-breaking space.
    assert stored_name(api, " 　Ana  ") == "Ana"


def test_r4_zero_width_characters_are_kept(api):
    # D10.
    assert stored_name(api, "​Ana​") == "​Ana​"


def test_r4_zero_width_only_name_is_one_character(api):
    # D10, D11.
    assert stored_name(api, "​") == "​"


def test_r4_inner_tabs_and_newlines_are_kept(api):
    # D12.
    assert stored_name(api, "Ana\tB\nC  D") == "Ana\tB\nC  D"


def test_r4_forty_code_points_outside_bmp_are_accepted(api):
    # D11: length in code points.
    name = "\U0001F600" * 40
    assert stored_name(api, name) == name


def test_r4_forty_code_points_with_combining_marks_are_accepted(api):
    # D11: "e" + combining acute = 2 code points.
    name = "é" * 20
    assert stored_name(api, name) == name


@pytest.mark.parametrize(
    "name",
    [
        "N" * 41,
        "  " + "N" * 41 + "  ",
        "\U0001F600" * 41,
        "é" * 20 + "e",
        "N" * 100,
    ],
)
def test_r4_more_than_forty_characters_is_invalid_name(api, rb, name):
    seed(api)
    api.fails(lambda: api.post(rb.body(booked_by=name)), 422, "invalid_name")


@pytest.mark.parametrize("name", ["", " ", "     ", "\t\n \r", " ", "　 "])
def test_r4_empty_or_whitespace_only_name_is_invalid_name(api, rb, name):
    # R4; D10 for Unicode spaces.
    seed(api)
    api.fails(lambda: api.post(rb.body(booked_by=name)), 422, "invalid_name")
