"""R1. List rooms."""

ROOMS = [
    {"id": 1, "name": "Quiet Room A", "capacity": 2},
    {"id": 2, "name": "Quiet Room B", "capacity": 2},
    {"id": 3, "name": "Group Room C", "capacity": 6},
    {"id": 4, "name": "Group Room D", "capacity": 8},
]


def test_r1_lists_the_four_rooms_in_id_order(client):
    resp = client.get("/api/rooms")
    assert resp.status_code == 200
    assert resp.json() == ROOMS


def test_r1_rooms_do_not_change_after_bookings(api):
    api.book(room_id=3)
    api.book(room_id=4, start="12:00", end="13:00")
    resp = api.client.get("/api/rooms")
    assert resp.status_code == 200
    assert resp.json() == ROOMS
