.PHONY: test lint typecheck all

test:
	uv run pytest

lint:
	uv run ruff check --fix

typecheck:
	uv run pyright src/*

all: lint test typecheck
