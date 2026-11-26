"""Converts rows from the old booking system's export (legacy/old_bookings.csv)
into the format of the new backend.

Written years ago for the old system. Nobody remembers every case it handles, and it
has no tests. The plan is to import the old bookings next term, so this code has to
be made safe to change first.

Run it on the sample export:
    python -m legacy.old_format legacy/old_bookings.csv
"""

from collections.abc import Mapping

ROOMS = {"Room A": 1, "Room B": 2, "Room C": 3, "Room D": 4}

# Old time format: "H:MM", optionally followed by a single space and "AM" or "PM".
TIME_MARKER_SEPARATOR = " "
TIME_SEPARATOR = ":"
PM_MARKER = "PM"
PM_HOUR_OFFSET = 12

# Old date format: "M/D/YYYY" or "M/D/YY".
OLD_DATE_SEPARATOR = "/"
SHORT_YEAR_LENGTH = 2
SHORT_YEAR_CENTURY = "20"

# New formats: "YYYY-MM-DD" and "HH:MM", with two-digit parts padded with zeros.
NEW_DATE_SEPARATOR = "-"
PADDED_WIDTH = 2


def to_24h(text: str) -> str:
    """Convert an old time such as "1:00 PM" to "HH:MM", as the old system did.

    Only an exact "PM" after a single space adds 12 hours; anything else, including
    "AM", "pm" or no marker, keeps the hour. The minutes are copied as written.
    Raises ValueError if the hour is not a number, and IndexError if there is no colon.
    """
    parts = text.strip().split(TIME_MARKER_SEPARATOR)
    clock = parts[0].split(TIME_SEPARATOR)
    hour = int(clock[0])
    minutes = clock[1]
    if len(parts) > 1 and parts[1] == PM_MARKER:
        hour = hour + PM_HOUR_OFFSET
    return str(hour).zfill(PADDED_WIDTH) + TIME_SEPARATOR + minutes


def parse_old_row(row: Mapping[str, str]) -> dict[str, int | str]:
    """Convert one row of the old export into a POST /api/bookings body.

    The row has the columns "room", "day" ("M/D/YYYY" or "M/D/YY"), "from", "to" and
    "who". Raises KeyError for a missing column or an unknown room, IndexError for a
    day without three parts or an empty name, and ValueError for a bad time.
    """
    room = ROOMS[row["room"].strip()]
    day_parts = row["day"].strip().split(OLD_DATE_SEPARATOR)
    month = day_parts[0]
    day = day_parts[1]
    year = day_parts[2]
    if len(year) == SHORT_YEAR_LENGTH:
        year = SHORT_YEAR_CENTURY + year
    date = (
        year
        + NEW_DATE_SEPARATOR
        + month.zfill(PADDED_WIDTH)
        + NEW_DATE_SEPARATOR
        + day.zfill(PADDED_WIDTH)
    )
    name = row["who"].strip()
    name = name[0].upper() + name[1:]
    return {
        "room_id": room,
        "date": date,
        "start": to_24h(row["from"]),
        "end": to_24h(row["to"]),
        "booked_by": name,
    }


if __name__ == "__main__":
    import csv
    import sys

    with open(sys.argv[1], newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            print(parse_old_row(row))
