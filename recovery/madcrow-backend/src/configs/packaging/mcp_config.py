from pydantic import Field
from pydantic_settings import BaseSettings


class MCPConfig(BaseSettings):
    """
    MCP-related configurations for the application
    """

    MCP_APP_NAME: str = Field(
        description="Name of the MCP application",
        default="Beco-MCP-Server",
    )
    MCP_APP_INSTRUCTION: str = Field(
        description="Instructions or description for the MCP application",
        default="Default instructions for MCP application.",
    )
    MCP_APP_VERSION: str = Field(
        description="Version of the MCP application",
        default="1.0.0",
    )
