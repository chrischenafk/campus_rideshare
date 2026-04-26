# Campus RideShare Matcher MVP (Notre Dame)

This project is a Python command-line MVP that matches Notre Dame students into shared Uber groups when they are leaving campus for breaks or trips. The app is intentionally simple: it reads ride requests from a CSV file, validates campus meetup locations against a separate editable list, checks compatibility, and prints matched groups plus unmatched students. It is an offline matcher only and does not attempt to book rides.

The matching logic uses four rules. Two students are compatible only if they have the same trip date, the same destination, share at least one meetup location, and have a time overlap of at least 15 minutes between earliest and latest departure times. A greedy grouping strategy then builds sensible groups while enforcing the Uber rider limit of 6 people per group. For each group, the output includes destination, rider names, shared meeting location, meeting time, and a randomly selected rider who calls the Uber.

Allowed destinations are currently restricted to `ORD`, `MDW`, and `SBN`. Meetup locations are loaded from `campus_locations.txt` and can be edited there without changing code.

The pairwise compatibility phase compares many request pairs, so runtime grows roughly as `O(n^2)`. Timing analysis was measured using synthetic datasets and averages over 5 trials:
- Small dataset (`n=20`): total ~`0.000100s`
- Large dataset (`n=500`): total ~`0.036723s`

These results align with expected quadratic growth as input size increases.

## Files

- `README.md`
- `Makefile`
- `parser.py`
- `matching.py`
- `timing.py`
- `tests/`
- `campus_locations.txt`
- `data/demo_requests.csv`

## CSV Input Schema

`name,destination,willing_areas,date,earliest,latest`

Example row:

`Alice,ORD,"Library Circle;Main Circle",2026-05-10,14:00,15:30`

## Commands

- `make test` - run unit tests
- `make demo` - run matcher on sample demo CSV
- `make timing` - run timing analysis for small and large datasets

## Out of Scope

- Real Uber API integration
- Lyft support (MVP assumes Uber only)
- Pricing/fare estimation
- Authentication, maps, geocoding, traffic, or route optimization
