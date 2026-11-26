"""Request and booking shapes for RoomBook (spec sections 2 and 4)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Room:
    id: int
    name: str
    capacity: int

    def to_dict(self) -> dict:
        """A room as section 4 returns it: exactly id, name, capacity."""
        return {"id": self.id, "name": self.name, "capacity": self.capacity}


@dataclass(frozen=True)
class Booking:
    id: int
    room_id: int
    date: str
    start: str
    end: str
    booked_by: str

    def to_dict(self) -> dict:
        """A booking as section 4 returns it: exactly the six fields."""
        return {
            "id": self.id,
            "room_id": self.room_id,
            "date": self.date,
            "start": self.start,
            "end": self.end,
            "booked_by": self.booked_by,
        }


@dataclass(frozen=True)
class BookingRequest:
    """A POST /api/bookings body that has passed R3 to R6, with booked_by trimmed (R4).

    Only the overlap check (R7) is left, done together with the save.
    """

    room_id: int
    date: str
    start: str
    end: str
    booked_by: str

    def to_dict(self) -> dict:
        return {
            "room_id": self.room_id,
            "date": self.date,
            "start": self.start,
            "end": self.end,
            "booked_by": self.booked_by,
        }
