#!/bin/sh
set -e

uv run ruff check src/
uv run python -m pytest tests/ --tb=short -q
