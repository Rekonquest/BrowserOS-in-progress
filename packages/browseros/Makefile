.PHONY: help install test test-verbose test-coverage lint format security-scan type-check clean all

help:
	@echo "BrowserOS Build System - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install          Install dependencies with uv"
	@echo ""
	@echo "Testing:"
	@echo "  make test             Run test suite"
	@echo "  make test-verbose     Run tests with verbose output"
	@echo "  make test-coverage    Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make lint             Run linters (ruff)"
	@echo "  make format           Format code (ruff format)"
	@echo "  make type-check       Run type checker (pyright)"
	@echo "  make security-scan    Run security vulnerability scan"
	@echo ""
	@echo "Maintenance:"
	@echo "  make clean            Remove generated files"
	@echo "  make all              Run all checks (lint, type-check, test, security)"

install:
	uv sync --all-extras --dev

test:
	uv run pytest

test-verbose:
	uv run pytest -vv

test-coverage:
	uv run pytest --cov=build --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

lint:
	uv run ruff check .

format:
	uv run ruff format .
	uv run ruff check --fix .

type-check:
	uv run pyright

security-scan:
	@echo "Running pip-audit for dependency vulnerabilities..."
	uv run pip-audit --desc
	@echo ""
	@echo "Security scan complete!"

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml
	@echo "Cleaned generated files"

all: lint type-check test security-scan
	@echo ""
	@echo "✅ All checks passed!"
