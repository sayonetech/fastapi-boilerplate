from pydantic import Field
from pydantic_settings import BaseSettings


class DeploymentConfig(BaseSettings):
    """
    Configuration settings for application deployment
    """

    DEBUG: bool = Field(
        description="Enable debug mode for additional logging and development features",
        default=False,
    )

    DEPLOY_ENV: str = Field(
        description="Deployment environment (e.g., 'PRODUCTION', 'DEVELOPMENT'), default to PRODUCTION",
        default="PRODUCTION",
    )

    BACKEND_APP_BIND_ADDRESS: str = Field(
        description="Host address to bind the backend application to",
        default="0.0.0.0",
    )

    BACKEND_APP_PORT: int = Field(
        description="Port number to bind the backend application to",
        default=5001,
    )
