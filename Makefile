.PHONY: install lint type test layers check live
PY := .venv/bin

install:
	python3 -m venv .venv && $(PY)/pip install -q -e ".[dev]"

lint:
	$(PY)/ruff check . && $(PY)/ruff format --check .

type:
	$(PY)/mypy

layers:
	$(PY)/lint-imports

test:
	$(PY)/pytest --cov --cov-report=term-missing

check: lint type layers test

live:
	RUN_LIVE=1 $(PY)/pytest -m live -v
