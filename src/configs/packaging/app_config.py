from pydantic import Field
from pydantic_settings import BaseSettings


class APPConfig(BaseSettings):
    """
    APP-related configurations
    """

    APP_NAME: str = Field(
        description="Name of the APP application",
        default="Beco-API-Server",
    )
    APP_INSTRUCTION: str = Field(
        description="Instructions or description for the APP application",
        default="Default instructions for APP application.",
    )
    APP_VERSION: str = Field(
        description="Version of the APP application",
        default="0.0.0",
    )
