"""Helpers for the acceptance tests. Every expected value comes from docs/spec.md.

The helpers are exposed as fixtures so this folder needs no package imports and never
imports app at module level.
"""

import pytest

DATE = "2031-03-14"
BOOKING_FIELDS = {"id", "room_id", "date", "start", "end", "booked_by"}


def body(**overrides):
    """A valid POST /api/bookings body (spec section 4), with fields replaced."""
    data = {
        "room_id": 1,
        "date": DATE,
        "start": "09:00",
        "end": "10:30",
        "booked_by": "Ana",
    }
    data.update(overrides)
    return data


def without(field):
    data = body()
    del data[field]
    return data


class Api:
    """Small wrapper around a TestClient for the section 4 endpoints."""

    def __init__(self, client):
        self.client = client

    # Requests -------------------------------------------------------------------

    def post(self, data):
        return self.client.post("/api/bookings", json=data)

    def post_raw(self, raw, content_type="application/json"):
        if isinstance(raw, str):
            raw = raw.encode("utf-8")
        return self.client.post(
            "/api/bookings", content=raw, headers={"Content-Type": content_type}
        )

    def get(self, query):
        return self.client.get("/api/bookings" + query)

    def delete(self, booking_id):
        return self.client.delete(f"/api/bookings/{booking_id}")

    # Assertions -----------------------------------------------------------------

    def book(self, **overrides):
        """Create a booking that must succeed (201) and return it."""
        data = body(**overrides)
        resp = self.post(data)
        assert resp.status_code == 201, resp.text
        booking = resp.json()
        check_booking(booking, data)
        return booking

    def bookings(self, date=DATE, room_id=None):
        """GET /api/bookings for a date (and room) that must succeed (200)."""
        query = f"?date={date}"
        if room_id is not None:
            query += f"&room_id={room_id}"
        resp = self.get(query)
        assert resp.status_code == 200, resp.text
        result = resp.json()
        assert isinstance(result, list)
        return result

    def snapshot(self, dates):
        return {d: self.bookings(d) for d in dates}

    def fails(self, send, status, code, dates=(DATE,)):
        """Run send(); it must fail with status and code (R9 body) and change nothing
        in the bookings of the given dates (R9)."""
        before = self.snapshot(dates)
        resp = send()
        assert_error(resp, status, code)
        after = self.snapshot(dates)
        assert after == before
        return resp


def check_booking(booking, data):
    """A booking has exactly six fields (section 4) and the values sent, with the name
    trimmed (R4)."""
    assert isinstance(booking, dict)
    assert set(booking) == BOOKING_FIELDS
    assert isinstance(booking["id"], int) and not isinstance(booking["id"], bool)
    assert booking["room_id"] == data["room_id"]
    assert booking["date"] == data["date"]
    assert booking["start"] == data["start"]
    assert booking["end"] == data["end"]
    assert booking["booked_by"] == data["booked_by"].strip()


def assert_error(resp, status, code):
    """R9: the status, and a body with exactly the keys error and message."""
    assert resp.status_code == status, resp.text
    payload = resp.json()
    assert isinstance(payload, dict)
    assert set(payload) == {"error", "message"}
    assert payload["error"] == code


@pytest.fixture
def api(client):
    return Api(client)


@pytest.fixture
def api_for(new_client):
    """api_for("a.db") gives an Api on that database file; calling it again with the
    same name restarts the backend on the same file (R10)."""
    return lambda name="test.db": Api(new_client(name))


@pytest.fixture
def rb():
    """Module-level helpers, so test files need not import this conftest."""

    class Helpers:
        DATE = DATE
        body = staticmethod(body)
        without = staticmethod(without)
        check_booking = staticmethod(check_booking)
        assert_error = staticmethod(assert_error)

    return Helpers
