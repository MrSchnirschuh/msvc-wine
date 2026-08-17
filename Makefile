.PHONY: test lint format

test:
	python -m pytest -q

lint:
	python -m ruff check .

format:
	python -m ruff format .
