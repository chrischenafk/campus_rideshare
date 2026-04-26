import argparse
import random

from parser import load_requests


def format_minutes(total_minutes):
    """Format minutes since midnight as HH:MM.

    Args:
        total_minutes: Integer minute offset from 00:00.

    Returns:
        Zero-padded time string in 24-hour HH:MM format.
    """
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def time_overlap_minutes(first, second):
    """Compute overlap window between two rider availability ranges.

    Args:
        first: First rider request dictionary.
        second: Second rider request dictionary.

    Returns:
        Number of overlapping minutes (0 if no overlap).
    """
    start = max(first["earliest_minutes"], second["earliest_minutes"])
    end = min(first["latest_minutes"], second["latest_minutes"])
    return max(0, end - start)


def compatible(first, second, min_overlap=15):
    """Check whether two riders can share a ride group.

    Args:
        first: First rider request dictionary.
        second: Second rider request dictionary.
        min_overlap: Minimum required overlap in minutes.

    Returns:
        True when destination, location, and time compatibility all pass.
    """
    if first["date"] != second["date"]:
        return False

    if first["destination"] != second["destination"]:
        return False

    if not (first["willing_areas"] & second["willing_areas"]):
        return False

    return time_overlap_minutes(first, second) >= min_overlap


def build_compatibility_graph(requests, min_overlap=30):
    """Build an undirected compatibility graph by request index.

    Args:
        requests: List of validated rider request dictionaries.
        min_overlap: Minimum required overlap in minutes.

    Returns:
        Dict mapping request index to a set of compatible indexes.
    """
    # Initialize an empty graph with one entry for each request.    
    graph = {index: set() for index in range(len(requests))}
    # Iterate over all pairs of requests and add edges to the graph if the requests are compatible.
    for left in range(len(requests)):
        for right in range(left + 1, len(requests)):
            # If the requests are compatible, add an edge to the graph.
            if compatible(requests[left], requests[right], min_overlap=min_overlap):
                # Add an edge from the left request to the right request.
                graph[left].add(right)
                # Add an edge from the right request to the left request.
                graph[right].add(left)
    return graph


def group_meeting_details(group_members):
    """Determine a shared meeting location and time for a group.

    Args:
        group_members: List of rider requests already confirmed compatible.

    Returns:
        Tuple of (meeting_location, meeting_time_hhmm).
    """
    #Initalize the shared areas and overlap start and end times to the first member's values.
    shared_areas = set(group_members[0]["willing_areas"])
    overlap_start = group_members[0]["earliest_minutes"]
    overlap_end = group_members[0]["latest_minutes"]

    for member in group_members[1:]:
        #Loop thorugh remaining members and update the shared areas and overlap start and end times.
        shared_areas &= member["willing_areas"]
        overlap_start = max(overlap_start, member["earliest_minutes"])
        overlap_end = min(overlap_end, member["latest_minutes"])

    # Choose a random meeting location from the shared areas.
    meeting_location = random.choice(sorted(shared_areas)) if shared_areas else "N/A"
    # Format the meeting time as HH:MM.
    meeting_time = format_minutes(overlap_start if overlap_start <= overlap_end else overlap_end)

    return meeting_location, meeting_time


def can_join_group(candidate, group_members, min_overlap):
    """Check if a candidate rider fits with every current group member.

    Args:
        candidate: Candidate rider request.
        group_members: Existing group member request dictionaries.
        min_overlap: Minimum overlap threshold in minutes.

    Returns:
        True if candidate is pairwise compatible with all group members.
    """
    return all(compatible(candidate, member, min_overlap=min_overlap) for member in group_members)


def form_groups(requests, max_group_size=6, min_overlap=15, seed=42):
    """Greedily build ride groups up to Uber's six-rider cap.

    Args:
        requests: List of validated rider requests.
        max_group_size: Maximum riders per group (hard-capped to 6 by caller).
        min_overlap: Minimum time overlap in minutes.
        seed: Deterministic seed for uber_caller selection.

    Returns:
        Tuple of (groups, unmatched_entries).
    """
    # Build the compatibility graph and initlaize unassigned requests and groups.
    graph = build_compatibility_graph(requests, min_overlap=min_overlap)
    unassigned = set(range(len(requests)))
    groups = []

    while unassigned: #While there are still unassigned requests
        #Start with the first unassigned request
        base_index = min(unassigned)
        base_request = requests[base_index]
        # Prefer candidates with larger overlap to keep groups coherent
        # Sort the compatible neighbors by the time overlap in descending order
        compatible_neighbors = sorted(
            graph[base_index] & unassigned,
            key=lambda i: time_overlap_minutes(base_request, requests[i]),
            reverse=True,
        )

        # Initialize the current group with the base request
        current_group = [base_index]
        #Loop though to find compatible neighbors
        for candidate in compatible_neighbors:
            #Check if candidate can join the group
            if len(current_group) >= max_group_size:
                break
            if candidate in current_group:
                continue
            candidate_request = requests[candidate]
            if can_join_group(candidate_request, [requests[i] for i in current_group], min_overlap):
                current_group.append(candidate)

        #Cleanup: remove the members from the unassigned set
        for member_index in current_group:
            unassigned.discard(member_index)

        #Check to make sure group has more than one member
        if len(current_group) > 1:
            #Form group meeting details
            members = [requests[index] for index in current_group]
            meeting_location, meeting_time = group_meeting_details(members)
            rider_names = [member["name"] for member in members]
            random_choice = random.Random(seed + len(groups))
            uber_caller = random_choice.choice(rider_names)
            groups.append(
                {
                    "group_number": len(groups) + 1,
                    "date": members[0]["date"],
                    "destination": members[0]["destination"],
                    "rider_names": rider_names,
                    "meeting_location": meeting_location,
                    "meeting_time": meeting_time,
                    "uber_caller": uber_caller,
                }
            )
        else:
            # Put single riders back into unmatched output only.
            continue

    #Rebuilds the unmatched list
    grouped_names = {name for group in groups for name in group["rider_names"]}
    unmatched = []
    for request in requests:
        if request["name"] not in grouped_names:
            unmatched.append({"name": request["name"], "reason": "No compatible riders"})

    return groups, unmatched


def print_results(groups, unmatched):
    """Print matcher output in human-readable CLI format.

    Args:
        groups: Group dictionaries produced by form_groups.
        unmatched: Unmatched rider dictionaries with reasons.

    Returns:
        None.
    """
    if groups:
        print("Matched Groups")
        print("--------------")
        for group in groups:
            print(f"Group {group['group_number']}")
            print(f"  Date: {group['date']}")
            print(f"  Destination: {group['destination']}")
            print(f"  Riders: {', '.join(group['rider_names'])}")
            print(f"  Meeting Location: {group['meeting_location']}")
            print(f"  Meeting Time: {group['meeting_time']}")
            print(f"  Uber Caller: {group['uber_caller']}")
            print("")
    else:
        print("Matched Groups")
        print("--------------")
        print("No groups formed.\n")

    print("Unmatched Students")
    print("------------------")
    if unmatched:
        for entry in unmatched:
            print(f"- {entry['name']}: {entry['reason']}")
    else:
        print("None")


def main():
    """Parse CLI arguments, run matching flow, and print results.

    Args:
        None.

    Returns:
        Process exit code integer (0 for success, 1 for validation errors).
    """
    cli = argparse.ArgumentParser(description="Notre Dame CSV RideShare matcher MVP")
    cli.add_argument("--input", default="data/demo_requests.csv", help="Path to request CSV")
    cli.add_argument(
        "--locations",
        default="campus_locations.txt",
        help="Path to campus locations file",
    )
    cli.add_argument("--max-group-size", type=int, default=6)
    cli.add_argument("--min-overlap", type=int, default=15)
    args = cli.parse_args()

    requests, errors = load_requests(args.input, args.locations)
    if errors:
        print("Input validation errors:")
        for error in errors:
            print(f"- {error}")
        return 1

    groups, unmatched = form_groups(
        requests,
        max_group_size=min(6, args.max_group_size),
        min_overlap=args.min_overlap,
    )
    print_results(groups, unmatched)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
