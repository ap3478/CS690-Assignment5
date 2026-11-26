"""R10. The application (spec section 3, D17)."""

from pathlib import Path

import pytest

DATE = "2031-03-14"
FRONTEND = Path(__file__).resolve().parents[2] / "frontend"
ROOMS = [
    {"id": 1, "name": "Quiet Room A", "capacity": 2},
    {"id": 2, "name": "Quiet Room B", "capacity": 2},
    {"id": 3, "name": "Group Room C", "capacity": 6},
    {"id": 4, "name": "Group Room D", "capacity": 8},
]


@pytest.mark.parametrize("path,filename", [("/", "index.html"), ("/app.js", "app.js"), ("/styles.css", "styles.css")])
def test_r10_serves_the_page_files(client, path, filename):
    resp = client.get(path)
    assert resp.status_code == 200
    assert resp.content == (FRONTEND / filename).read_bytes()


def test_r10_creates_the_database_file_at_db_path(api_for, tmp_path):
    api_for("created.db")
    assert (tmp_path / "created.db").is_file()


def test_r10_fresh_file_has_the_four_rooms_and_no_bookings(api_for):
    api = api_for("fresh.db")
    assert api.client.get("/api/rooms").json() == ROOMS
    assert api.bookings(DATE) == []


def test_r10_restart_sees_saved_bookings(api_for):
    first = api_for("same.db")
    a = first.book(room_id=1, start="09:00", end="10:00", booked_by="Ana")
    b = first.book(room_id=3, date="2031-03-15", start="14:00", end="16:00", booked_by="Bo")
    restarted = api_for("same.db")
    assert restarted.bookings(DATE) == [a]
    assert restarted.bookings("2031-03-15") == [b]


def test_r10_restart_does_not_duplicate_rooms(api_for):
    # D17: rooms are only added when the file has none.
    api_for("same.db")
    api_for("same.db")
    restarted = api_for("same.db")
    resp = restarted.client.get("/api/rooms")
    assert resp.status_code == 200
    assert resp.json() == ROOMS


def test_r10_restart_sees_cancellations(api_for):
    first = api_for("same.db")
    keep = first.book(start="08:00", end="09:00")
    gone = first.book(start="09:00", end="10:00")
    assert first.delete(gone["id"]).status_code == 204
    restarted = api_for("same.db")
    assert restarted.bookings(DATE) == [keep]


def test_r10_restart_still_rejects_overlap_with_saved_booking(api_for, rb):
    first = api_for("same.db")
    first.book(room_id=2, start="10:00", end="12:00")
    restarted = api_for("same.db")
    restarted.fails(lambda: restarted.post(rb.body(room_id=2, start="11:00", end="12:00")), 409, "overlap")


def test_r10_different_files_do_not_share_bookings(api_for):
    a = api_for("a.db")
    b = api_for("b.db")
    booking = a.book(room_id=1, start="09:00", end="10:00")
    assert b.bookings(DATE) == []
    assert a.bookings(DATE) == [booking]


def test_r10_different_files_do_not_share_overlap_checks(api_for):
    a = api_for("a.db")
    b = api_for("b.db")
    in_a = a.book(room_id=1, start="09:00", end="10:00", booked_by="Ana")
    in_b = b.book(room_id=1, start="09:00", end="10:00", booked_by="Bo")
    assert a.bookings(DATE) == [in_a]
    assert b.bookings(DATE) == [in_b]


def test_r10_cancel_in_one_file_does_not_touch_another(api_for):
    a = api_for("a.db")
    b = api_for("b.db")
    booking = a.book()
    b.fails(lambda: b.delete(booking["id"]), 404, "booking_not_found")
    assert a.bookings(DATE) == [booking]
