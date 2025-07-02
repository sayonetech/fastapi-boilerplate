from typing import Any

from fastmcp import FastMCP

from ..beco_app import BecoApp


def is_enabled() -> bool:
    return True


class McpAppWrapper:
    """
    A wrapper class for the FastMCP  that addresses the issue where the global
    `mcp_wrapper` variable cannot be updated when a new FastMCP instance is returned.


    Attributes:
        _mcp_app (Optional[FastMCP]): The actual FastMCP instance. It remains None until
                               initialized with the `initialize` method.

    Methods:
        initialize(app): Initializes FastMCP if it hasn't been initialized already.
        __getattr__(item): Delegates attribute access to the FastMCP, raising an error
                           if the app is not initialized.
    """

    def __init__(self) -> None:
        self._mcp_app: FastMCP | None = None

    def initialize(self, app: FastMCP) -> None:
        if self._mcp_app is None:
            self._mcp_app = app
            # Register tools after initialization
            self._register_tools()

    def _register_tools(self) -> None:
        """Register all MCP tools after the server is initialized."""
        if self._mcp_app is None:
            return

        # Import and register tools here to ensure MCP is initialized first
        from ..mcp.prompts.site_prompts import (  # noqa: F401
            site_information_assistant,
            venue_contact_assistant,
            venue_navigation_help,
        )
        from ..mcp.tools.locations import get_locations  # noqa: F401
        from ..mcp.tools.sites import get_site_info  # noqa: F401

        # The tools will be automatically registered via the decorators
        # when the modules are imported after MCP is initialized

    def __getattr__(self, item: str) -> Any:
        if self._mcp_app is None:
            raise RuntimeError("Mcp app is not initialized. Call init_app first.")
        return getattr(self._mcp_app, item)


mcp_wrapper = McpAppWrapper()


def init_app(app: BecoApp) -> None:
    global mcp_wrapper
    mcp_app = app.state.mcp_app
    # Create the ASGI app
    app.mount("/mcp", mcp_app)
    mcp_wrapper.initialize(app.state.mcp)
