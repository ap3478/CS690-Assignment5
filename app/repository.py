"""Data access for RoomBook. The only module that imports sqlite3 or holds SQL.

Every method opens its own connection and closes it before returning, so no
connection is ever shared between requests or threads.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing

# Spec section 2: the four rooms. They are added only when the file has no rooms (D17).
ROOMS = [
    (1, "Quiet Room A", 2),
    (2, "Quiet Room B", 2),
    (3, "Group Room C", 6),
    (4, "Group Room D", 8),
]

BUSY_TIMEOUT_SECONDS = 30.0

BOOKING_COLUMNS ='id, room_id, date, "start", "end", booked_by'


class Repository:
    """SQLite storage for rooms and bookings in the one file at db_path."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        # isolation_level=None: autocommit, so this class runs its own transactions.
        # timeout: how long to wait for another request's write lock (BEGIN IMMEDIATE)
        # before giving up, longer than the 5-second default so bursts of bookings queue.
        conn = sqlite3.connect(self.db_path, isolation_level=None, timeout=BUSY_TIMEOUT_SECONDS)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create the tables if missing and add the rooms if the file has none."""
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS rooms ("
                    " id INTEGER PRIMARY KEY,"
                    " name TEXT NOT NULL,"
                    " capacity INTEGER NOT NULL)"
                )
                # AUTOINCREMENT: an id is never reused, even after a cancel (D14).
                conn.execute(
                    "CREATE TABLE IF NOT EXISTS bookings ("
                    " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    " room_id INTEGER NOT NULL,"
                    " date TEXT NOT NULL,"
                    ' "start" TEXT NOT NULL,'
                    ' "end" TEXT NOT NULL,'
                    " booked_by TEXT NOT NULL)"
                )
                (count,) = conn.execute("SELECT COUNT(*) FROM rooms").fetchone()
                if count == 0:
                    conn.executemany(
                        "INSERT INTO rooms (id, name, capacity) VALUES (?, ?, ?)", ROOMS
                    )
                conn.execute("COMMIT")
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise

    def list_rooms(self) -> list[dict]:
        """All rooms, ordered by id."""
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT id, name, capacity FROM rooms ORDER BY id").fetchall()
        return [dict(row) for row in rows]

    def list_bookings(self, date: str, room_id: int | None = None) -> list[dict]:
        """Bookings on date (and in room_id, if given), ordered by room_id then start."""
        sql = f"SELECT {BOOKING_COLUMNS} FROM bookings WHERE date = ?"
        params: list = [date]
        if room_id is not None:
            sql += " AND room_id = ?"
            params.append(room_id)
        sql += ' ORDER BY room_id, "start"'
        with closing(self._connect()) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]

    def create_booking_if_free(
        self, room_id: int, date: str, start: str, end: str, booked_by: str
    ) -> dict | None:
        """Check for overlap and save in one locked step (D13).

        Returns the new booking, or None when it overlaps an existing booking for the
        same room on the same date. Nothing is saved when it returns None or raises.
        """
        with closing(self._connect()) as conn:
            conn.execute("BEGIN IMMEDIATE")
            try:
                clash = conn.execute(
                    "SELECT 1 FROM bookings"
                    ' WHERE room_id = ? AND date = ? AND "start" < ? AND ? < "end"'
                    " LIMIT 1",
                    (room_id, date, end, start),
                ).fetchone()
                if clash is not None:
                    conn.execute("ROLLBACK")
                    return None
                cur = conn.execute(
                    'INSERT INTO bookings (room_id, date, "start", "end", booked_by)'
                    " VALUES (?, ?, ?, ?, ?)",
                    (room_id, date, start, end, booked_by),
                )
                new_id = cur.lastrowid
                conn.execute("COMMIT")
            except BaseException:
                if conn.in_transaction:
                    conn.execute("ROLLBACK")
                raise
        return {
            "id": new_id,
            "room_id": room_id,
            "date": date,
            "start": start,
            "end": end,
            "booked_by": booked_by,
        }

    def delete_booking(self, booking_id: int) -> bool:
        """Remove the booking. True if one was removed, False if none had that id."""
        with closing(self._connect()) as conn:
            cur = conn.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
            return cur.rowcount > 0
