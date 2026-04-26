from matching import (
    compatible,
    form_groups,
    format_minutes,
    time_overlap_minutes,
)


def make_request(name, destination, areas, date, earliest, latest):
    """Build a request dictionary for matching tests.

    Args:
        name: Rider display name.
        destination: Destination airport code.
        areas: Iterable of meetup location names.
        date: Trip date in ISO YYYY-MM-DD format.
        earliest: Earliest departure minute.
        latest: Latest departure minute.

    Returns:
        Request dictionary matching parser output shape.
    """
    return {
        "name": name,
        "destination": destination,
        "date": date,
        "willing_areas": set(areas),
        "earliest_minutes": earliest,
        "latest_minutes": latest,
    }


def test_time_overlap_minutes_true_and_false():
    """Verify overlap math for both overlapping and disjoint windows."""
    alice = make_request("Alice", "ORD", {"Library Circle"}, "2026-05-10", 14 * 60, 15 * 60)
    ben = make_request("Ben", "ORD", {"Library Circle"}, "2026-05-10", 14 * 60 + 30, 16 * 60)
    chris = make_request("Chris", "ORD", {"Library Circle"}, "2026-05-10", 16 * 60, 17 * 60)

    assert time_overlap_minutes(alice, ben) == 30
    assert time_overlap_minutes(alice, chris) == 0


def test_compatible_true_and_false_cases():
    """Verify compatibility requires destination, location, and overlap."""
    alice = make_request("Alice", "ORD", {"Library Circle", "Main Circle"}, "2026-05-10", 840, 930)
    ben = make_request("Ben", "ORD", {"Library Circle"}, "2026-05-10", 870, 960)
    maya = make_request("Maya", "MDW", {"Library Circle"}, "2026-05-10", 870, 960)
    zack = make_request("Zack", "ORD", {"Sorin Ct"}, "2026-05-10", 870, 960)
    nina = make_request("Nina", "ORD", {"Library Circle"}, "2026-05-11", 870, 960)

    assert compatible(alice, ben, min_overlap=15) is True
    assert compatible(alice, maya, min_overlap=15) is False
    assert compatible(alice, zack, min_overlap=15) is False
    assert compatible(alice, nina, min_overlap=15) is False


def test_form_groups_enforces_max_six_and_group_output_fields():
    """Verify group size cap and required output fields are respected."""
    requests = [
        make_request(f"Rider{i}", "ORD", {"Library Circle"}, "2026-05-10", 14 * 60, 16 * 60)
        for i in range(1, 8)
    ]

    groups, unmatched = form_groups(requests, max_group_size=6, min_overlap=15, seed=7)

    assert len(groups) == 1
    assert len(groups[0]["rider_names"]) == 6
    assert groups[0]["date"] == "2026-05-10"
    assert groups[0]["destination"] == "ORD"
    assert groups[0]["meeting_location"] == "Library Circle"
    assert groups[0]["meeting_time"] == "14:00"
    assert groups[0]["uber_caller"] in groups[0]["rider_names"]
    assert len(unmatched) == 1
    assert unmatched[0]["name"] in {"Rider1", "Rider2", "Rider3", "Rider4", "Rider5", "Rider6", "Rider7"}


def test_form_groups_reports_unmatched_with_reason():
    """Verify incompatible riders are reported as unmatched with reason."""
    requests = [
        make_request("Alice", "ORD", {"Library Circle"}, "2026-05-10", 14 * 60, 15 * 60),
        make_request("Bob", "MDW", {"Library Circle"}, "2026-05-10", 14 * 60, 15 * 60),
    ]

    groups, unmatched = form_groups(requests, max_group_size=6, min_overlap=15, seed=11)

    assert groups == []
    assert len(unmatched) == 2
    reasons = {entry["reason"] for entry in unmatched}
    assert reasons == {"No compatible riders"}


def test_format_minutes():
    """Verify minute formatting always produces HH:MM text."""
    assert format_minutes(0) == "00:00"
    assert format_minutes(905) == "15:05"
