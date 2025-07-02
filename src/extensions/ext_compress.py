from ..beco_app import BecoApp
from ..configs import mcp_agent_config


def is_enabled() -> bool:
    return mcp_agent_config.API_COMPRESSION_ENABLED


def init_app(app: BecoApp):
    from fastapi.middleware.gzip import GZipMiddleware

    app.add_middleware(GZipMiddleware, minimum_size=500)
