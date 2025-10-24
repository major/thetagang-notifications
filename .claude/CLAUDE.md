# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Discord notification bot for ThetaGang trades. It fetches trading data from thetagang.com API and sends formatted notifications to Discord webhooks when trades are opened or closed.

## Development Commands

```bash
# Run tests
make test
# or directly:
uv run pytest

# Run linter (auto-fixes issues)
make lint
# or directly:
uv run ruff check --fix

# Run type checking
make typecheck
# or directly:
uv run pyright src/*

# Run all checks (lint, test, typecheck)
make all

# Run a single test
uv run pytest tests/test_trade.py::test_notify -v
```

## Project Structure

The codebase has been migrated from the root `thetagang_notifications/` directory to `src/thetagang_notifications/`. Key components:

- **src/thetagang_notifications/trade.py**: Core trade parsing and notification logic
- **src/thetagang_notifications/trade_math.py**: Mathematical calculations for options trading (break-even, returns, etc.)
- **src/thetagang_notifications/trade_queue.py**: Redis-based queue management for processing trades
- **src/thetagang_notifications/notification.py**: Discord webhook notification handling
- **src/thetagang_notifications/config.py**: Configuration and environment variables
- **src/thetagang_notifications/assets/trade_specs.yml**: Trade type specifications and definitions

## Key Architecture Patterns

### Trade Processing Flow
1. Trades are fetched from thetagang.com API (`TRADES_JSON_URL`)
2. Each trade is checked against Redis to avoid duplicate processing
3. Trade objects are created based on trade type specifications in `trade_specs.yml`
4. Notifications are formatted with calculations (break-even, returns, etc.) and sent to Discord

### Environment Variables
- `REDIS_HOST`, `REDIS_PORT`: Redis connection details
- `WEBHOOK_URL_TRADES`: Discord webhook URL for trade notifications
- `TRADES_API_KEY`: API key for thetagang.com
- `SKIPPED_USERS`: Comma-separated list of users to skip

### Testing
- Uses pytest with VCR for recording/replaying HTTP requests
- Fakeredis for Redis mocking in tests
- Test fixtures are in `tests/fixtures/` and cassettes in `tests/cassettes/`
- Coverage reporting enabled by default

## Dependencies

This project uses `uv` as the package manager with Python 3.13+. All dependencies are defined in `pyproject.toml`.