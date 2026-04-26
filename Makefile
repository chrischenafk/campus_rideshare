PYTHON=python3

.PHONY: test demo timing

# Run all unit tests quietly.
test:
	$(PYTHON) -m pytest tests -q

# Run matcher against bundled sample CSV.
demo:
	$(PYTHON) matching.py --input data/demo_requests.csv --locations campus_locations.txt

# Benchmark matcher runtime on synthetic datasets.
timing:
	$(PYTHON) timing.py
