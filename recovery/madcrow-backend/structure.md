my_fastapi_mcp_project/
├── .env                # Environment variables
├── .env.example        # Example environment variables
├── .gitignore
├── .pre-commit-config.yaml  # Pre-commit hooks for linting, security, etc.
├── .cursor/            # Cursor rules and settings
│   └── rules/
│       └── fastapi_mcp.mdc
├── Dockerfile          # Containerization
├── docker-compose.yml  # Docker orchestration
├── pyproject.toml      # Project metadata and dependencies (uv)
├── ruff.toml           # Ruff configuration
├── README.md
├── main.py             # FastAPI app entry point, MCP mounting
├── src/
│   ├── __init__.py
│   ├── dependencies.py # Shared dependencies (auth, tracing, etc.)
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── location.py # Location search endpoints
│   │   └── route.py    # Route creation endpoints
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py   # Pydantic config for env vars
│   │   └── security.py # Security utilities
│   ├── models/
│   │   ├── __init__.py
│   │   ├── location.py # Location data models
│   │   └── route.py    # Route data models
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── location.py # Pydantic schemas for location
│   │   └── route.py    # Pydantic schemas for route
│   ├── services/
│   │   ├── __init__.py
│   │   ├── location_service.py # Location business logic
│   │   └── route_service.py    # Route business logic
│   ├── tracing/
│   │   ├── __init__.py
│   │   └── opentelemetry.py    # OpenTelemetry setup
│   └── mcp/
│       ├── __init__.py
│       └── tools.py    # MCP tool registration and logic
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   ├── test_location.py
│   └── test_route.py
└── scripts/
    └── lint.sh         # Script for running Ruff, security checks, etc.
