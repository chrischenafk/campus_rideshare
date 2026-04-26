#timing.py: Makes synthetic requests and benchmarks the matching algorithm

import random
import statistics
import time

from matching import build_compatibility_graph, form_groups


# Benchmark against the same airport set accepted by parser.py.
DESTINATIONS = ["ORD", "MDW", "SBN"]
MEETUP_CHOICES = [
    "Main Circle",
    "Library Circle",
    "Wilson Dr / Bulla Rd",
    "Sorin Ct",
    "Cavanaugh Dr",
    "Moose Krause Cir",
    "Siegfried / Pasquerilla West Circle",
]
TRIP_DATES = [
    "2026-05-10",
    "2026-05-11",
    "2026-05-12",
    "2026-05-13",
]


def make_synthetic_request(index, rng):
    """Create one randomized synthetic request for timing tests.

    Args:
        index: Numeric suffix for student name.
        rng: random.Random instance used for deterministic generation.

    Returns:
        Request dictionary shaped like parser output.
    """
    start_hour = rng.randint(7, 19)
    start_minute = rng.choice([0, 15, 30, 45])
    earliest = start_hour * 60 + start_minute
    latest = earliest + rng.choice([30, 45, 60, 75, 90])
    areas = set(rng.sample(MEETUP_CHOICES, k=rng.randint(1, 3)))
    return {
        "name": f"Student{index}",
        "destination": rng.choice(DESTINATIONS),
        "date": rng.choice(TRIP_DATES),
        "willing_areas": areas,
        "earliest_minutes": earliest,
        "latest_minutes": min(latest, 23 * 60 + 59),
    }


def make_dataset(size, seed):
    """Create a synthetic request dataset of a given size.

    Args:
        size: Number of requests to generate.
        seed: Seed value for deterministic randomness.

    Returns:
        List of synthetic request dictionaries.
    """
    rng = random.Random(seed)
    return [make_synthetic_request(i, rng) for i in range(size)]


def benchmark_dataset(requests, trials=5):
    """Benchmark compatibility graph and grouping runtime averages.

    Args:
        requests: Input request list to benchmark.
        trials: Number of repeated timing trials.

    Returns:
        Dict with average seconds for graph, grouping, and total.
    """
    graph_times = []
    grouping_times = []
    total_times = []

    for trial in range(trials):
        trial_seed = 1000 + trial

        total_start = time.perf_counter()
        graph_start = time.perf_counter()
        _ = build_compatibility_graph(requests, min_overlap=15)
        graph_end = time.perf_counter()

        group_start = time.perf_counter()
        _groups, _unmatched = form_groups(
            requests,
            max_group_size=6,
            min_overlap=15,
            seed=trial_seed,
        )
        group_end = time.perf_counter()
        total_end = time.perf_counter()

        graph_times.append(graph_end - graph_start)
        grouping_times.append(group_end - group_start)
        total_times.append(total_end - total_start)

    return {
        "graph_avg": statistics.mean(graph_times),
        "grouping_avg": statistics.mean(grouping_times),
        "total_avg": statistics.mean(total_times),
    }


def print_result(label, result):
    """Print one benchmark result block.

    Args:
        label: Text label for the dataset size.
        result: Dict returned by benchmark_dataset.

    Returns:
        None.
    """
    print(f"{label}:")
    print(f"  build_graph_seconds: {result['graph_avg']:.6f}")
    print(f"  grouping_seconds:    {result['grouping_avg']:.6f}")
    print(f"  total_seconds:       {result['total_avg']:.6f}")


def main():
    """Run timing comparisons for small and large synthetic datasets.

    Args:
        None.

    Returns:
        None.
    """
    small = make_dataset(size=20, seed=42)
    large = make_dataset(size=500, seed=42)

    small_result = benchmark_dataset(small, trials=5)
    large_result = benchmark_dataset(large, trials=5)

    print("Timing Analysis (average across 5 trials)")
    print("----------------------------------------")
    print_result("Small dataset (n=20)", small_result)
    print_result("Large dataset (n=500)", large_result)


if __name__ == "__main__":
    main()
