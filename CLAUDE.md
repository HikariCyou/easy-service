# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture Overview

This is a microservices architecture with two main FastAPI services:

- **easywork-hr**: HR management service (port 8090)
- **easywork-ses**: Skills and employee services (port 8080)

Both services use:
- FastAPI framework with Tortoise ORM
- MySQL database backend
- Poetry for dependency management
- Shared architectural patterns and structure

## Common Development Commands

Each service has its own Makefile with identical commands. Navigate to either `easywork-hr/` or `easywork-ses/` directory first.

### Setup and Installation
```bash
make install          # Install dependencies via poetry
```

### Running Services
```bash
make start            # Start the FastAPI server
make run              # Alias for start
```

### Code Quality
```bash
make check            # Run all checks (format + lint)
make check-format     # Check code formatting (black + isort)
make format           # Format code (black + isort)
make lint             # Run ruff linting
```

### Testing
```bash
make test             # Run pytest test suite
```

### Database Operations
```bash
make migrate          # Generate migration files with aerich
make upgrade          # Apply migrations to database
make clean-db         # Delete migrations and SQLite files
```

### Docker
```bash
# From root directory
docker-compose up hr  # Start HR service
docker-compose up ses # Start SES service
```

## Code Structure Patterns

Both services follow identical structure:

```
app/
├── api/v1/           # API route definitions
├── controllers/      # Business logic controllers
├── core/            # Core functionality (auth, middleware, exceptions)
├── models/          # Tortoise ORM models
├── schemas/         # Pydantic schemas for API validation
├── service/         # Service layer (HistoryService)
└── settings/        # Configuration management
```

## Database Configuration

- Uses Tortoise ORM with MySQL backend
- Migration management via Aerich
- Database connections configured in `app/settings/config.py`
- Timezone: Asia/Tokyo

## Key Implementation Details

- Custom middleware for CORS, background tasks, and HTTP audit logging
- JWT authentication via `app/core/auth.py`
- Structured exception handling in `app/core/exceptions.py`
- Logging configuration via Loguru
- API versioning under `/api/v1/`

## Development Workflow

1. Make changes to code
2. Run `make check` to verify formatting and linting
3. Run `make test` to execute test suite
4. Use `make migrate` and `make upgrade` for database changes
5. Test locally with `make start`

## Service-Specific Notes

- **easywork-hr**: Manages employee data, contracts, join/leave processes
- **easywork-ses**: Handles skills management, business processes, and case management