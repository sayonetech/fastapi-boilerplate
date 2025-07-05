"""Main entry point for the Madcrow Backend Server."""

import uvicorn

from src.configs import madcrow_config

if __name__ == "__main__":
    uvicorn.run(
        "app:create_app",
        factory=True,
        host=madcrow_config.BACKEND_APP_BIND_ADDRESS,
        port=madcrow_config.BACKEND_APP_PORT,
        log_level="info",
        proxy_headers=True,
        reload=True,
    )
