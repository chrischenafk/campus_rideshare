import csv
from datetime import datetime

ALLOWED_DESTINATIONS = {"ORD", "MDW", "SBN"}


def parse_time_to_minutes(time_text):
    """Convert 24-hour HH:MM text into total minutes.

    Args:
        time_text: Time value in HH:MM format.

    Returns:
        Integer minutes since 00:00.

    Raises:
        ValueError: If the value is not valid HH:MM within a day.
    """
    parts = time_text.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid time format: {time_text}")

    try:
        hours = int(parts[0])
        minutes = int(parts[1])
    except ValueError as exc:
        raise ValueError(f"Invalid time format: {time_text}") from exc

    if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
        raise ValueError(f"Invalid time value: {time_text}")

    return hours * 60 + minutes


def parse_trip_date(date_text):
    """Validate and normalize a trip date in ISO YYYY-MM-DD format.

    Args:
        date_text: Date string in YYYY-MM-DD format.

    Returns:
        Normalized ISO date string.

    Raises:
        ValueError: If date value is missing or not valid ISO format.
    """
    cleaned = date_text.strip()
    if not cleaned:
        raise ValueError("Missing date")

    try:
        return datetime.strptime(cleaned, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise ValueError(f"Invalid date format: {date_text}") from exc


def load_allowed_locations(locations_path):
    """Load non-empty meetup locations from a text file.

    Args:
        locations_path: Path to newline-delimited meetup locations.

    Returns:
        Set of allowed meetup location strings.
    """
    allowed = set()
    with open(locations_path, "r", encoding="utf-8") as file_obj:
        for line in file_obj:
            location = line.strip()
            if location:
                allowed.add(location)
    return allowed


def parse_willing_areas(raw_areas):
    """Parse semicolon-delimited willing meetup areas into a set.

    Args:
        raw_areas: Raw CSV field containing one or more locations.

    Returns:
        Set of cleaned location strings.
    """
    areas = set()
    for area in raw_areas.split(";"):
        cleaned = area.strip()
        if cleaned:
            areas.add(cleaned)
    return areas


def load_requests(csv_path, locations_path):
    """Load and validate ride requests from CSV input.

    Args:
        csv_path: Path to the ride request CSV.
        locations_path: Path to the allowed meetup locations file.

    Returns:
        Tuple of (valid_requests, validation_errors).
    """
    allowed_locations = load_allowed_locations(locations_path)
    requests = []
    errors = []

    with open(csv_path, "r", newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row_number, row in enumerate(reader, start=2):
            try:
                name = (row.get("name") or "").strip()
                destination = (row.get("destination") or "").strip()
                trip_date = parse_trip_date(row.get("date") or "")
                willing_areas = parse_willing_areas(row.get("willing_areas") or "")
                earliest = parse_time_to_minutes(row.get("earliest") or "")
                latest = parse_time_to_minutes(row.get("latest") or "")

                if not name:
                    raise ValueError("Missing name")
                if not destination:
                    raise ValueError("Missing destination")
                # Keep destination values constrained to known airports.
                if destination not in ALLOWED_DESTINATIONS:
                    raise ValueError(f"Unknown destination: {destination}")
                if not willing_areas:
                    raise ValueError("Missing willing_areas")
                if earliest > latest:
                    raise ValueError("earliest must be <= latest")

                unknown = willing_areas - allowed_locations
                if unknown:
                    unknown_list = ", ".join(sorted(unknown))
                    raise ValueError(f"Unknown meetup location(s): {unknown_list}")

                requests.append(
                    {
                        "name": name,
                        "destination": destination,
                        "date": trip_date,
                        "willing_areas": willing_areas,
                        "earliest_minutes": earliest,
                        "latest_minutes": latest,
                    }
                )
            except ValueError as exc:
                errors.append(f"Row {row_number}: {exc}")

    return requests, errors
