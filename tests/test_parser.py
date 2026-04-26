import csv

import pytest

from parser import load_allowed_locations, load_requests, parse_time_to_minutes


def write_csv(path, rows):
    """Write request rows to a temporary CSV file for tests.

    Args:
        path: pathlib.Path for the CSV output file.
        rows: Iterable of row dictionaries using request schema keys.

    Returns:
        None.
    """
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=["name", "destination", "willing_areas", "date", "earliest", "latest"],
        )
        writer.writeheader()
        writer.writerows(rows)


def test_parse_time_to_minutes_valid():
    """Verify valid HH:MM values convert to expected minutes."""
    assert parse_time_to_minutes("00:00") == 0
    assert parse_time_to_minutes("14:30") == 870
    assert parse_time_to_minutes("23:59") == 1439


def test_parse_time_to_minutes_invalid():
    """Verify malformed and out-of-range times are rejected."""
    with pytest.raises(ValueError):
        parse_time_to_minutes("24:01")

    with pytest.raises(ValueError):
        parse_time_to_minutes("14-30")


def test_load_allowed_locations_ignores_blank_lines(tmp_path):
    """Verify location loader strips blanks and whitespace-only lines."""
    locations_path = tmp_path / "locations.txt"
    locations_path.write_text(
        "Library Circle\n\nWilson Dr / Bulla Rd\n  \nMain Circle\n",
        encoding="utf-8",
    )

    allowed = load_allowed_locations(str(locations_path))

    assert allowed == {"Library Circle", "Wilson Dr / Bulla Rd", "Main Circle"}


def test_load_requests_success(tmp_path):
    """Verify a valid row is parsed into normalized request fields."""
    locations_path = tmp_path / "locations.txt"
    locations_path.write_text(
        "Library Circle\nWilson Dr / Bulla Rd\nMain Circle\n",
        encoding="utf-8",
    )

    requests_path = tmp_path / "requests.csv"
    write_csv(
        requests_path,
        [
            {
                "name": "Alice",
                "destination": "ORD",
                "willing_areas": "Library Circle;Main Circle",
                "date": "2026-05-10",
                "earliest": "14:00",
                "latest": "15:30",
            }
        ],
    )

    requests, errors = load_requests(str(requests_path), str(locations_path))

    assert errors == []
    assert len(requests) == 1
    assert requests[0]["name"] == "Alice"
    assert requests[0]["destination"] == "ORD"
    assert requests[0]["date"] == "2026-05-10"
    assert requests[0]["willing_areas"] == {"Library Circle", "Main Circle"}
    assert requests[0]["earliest_minutes"] == 840
    assert requests[0]["latest_minutes"] == 930


def test_load_requests_rejects_unknown_location(tmp_path):
    """Verify parser rejects meetup locations not in allowed list."""
    locations_path = tmp_path / "locations.txt"
    locations_path.write_text("Library Circle\nMain Circle\n", encoding="utf-8")

    requests_path = tmp_path / "requests.csv"
    write_csv(
        requests_path,
        [
            {
                "name": "Bob",
                "destination": "MDW",
                "willing_areas": "Unknown Hall",
                "date": "2026-05-11",
                "earliest": "10:00",
                "latest": "11:00",
            }
        ],
    )

    requests, errors = load_requests(str(requests_path), str(locations_path))

    assert requests == []
    assert len(errors) == 1
    assert "Unknown meetup location" in errors[0]


def test_load_requests_rejects_unknown_destination(tmp_path):
    """Verify parser rejects destinations outside the airport allowlist."""
    locations_path = tmp_path / "locations.txt"
    locations_path.write_text("Library Circle\nMain Circle\n", encoding="utf-8")

    requests_path = tmp_path / "requests.csv"
    write_csv(
        requests_path,
        [
            {
                "name": "Bob",
                "destination": "LGA",
                "willing_areas": "Main Circle",
                "date": "2026-05-12",
                "earliest": "10:00",
                "latest": "11:00",
            }
        ],
    )

    requests, errors = load_requests(str(requests_path), str(locations_path))

    assert requests == []
    assert len(errors) == 1
    assert "Unknown destination" in errors[0]


def test_load_requests_rejects_invalid_date(tmp_path):
    """Verify parser rejects malformed date values."""
    locations_path = tmp_path / "locations.txt"
    locations_path.write_text("Library Circle\nMain Circle\n", encoding="utf-8")

    requests_path = tmp_path / "requests.csv"
    write_csv(
        requests_path,
        [
            {
                "name": "Bob",
                "destination": "ORD",
                "willing_areas": "Main Circle",
                "date": "05/12/2026",
                "earliest": "10:00",
                "latest": "11:00",
            }
        ],
    )

    requests, errors = load_requests(str(requests_path), str(locations_path))

    assert requests == []
    assert len(errors) == 1
    assert "Invalid date format" in errors[0]
