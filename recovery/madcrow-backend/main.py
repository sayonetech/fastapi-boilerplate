"""Main entry point for the Beco MCP Server."""

import uvicorn

from src.configs import mcp_agent_config

if __name__ == "__main__":
    uvicorn.run(
        "app:create_app",
        factory=True,
        host=mcp_agent_config.BACKEND_APP_BIND_ADDRESS,
        port=mcp_agent_config.BACKEND_APP_PORT,
        log_level="info",
        proxy_headers=True,
        reload=True,
    )
