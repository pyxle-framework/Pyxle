.PHONY: install test lint clean

install:
	pip install -e .[dev]

test:
	pytest

lint:
	ruff check pyxle/ tests/

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ dist/ *.egg-info/
