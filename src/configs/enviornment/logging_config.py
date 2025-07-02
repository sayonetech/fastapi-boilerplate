from pydantic import Field
from pydantic_settings import BaseSettings


class LoggingConfig(BaseSettings):
    """
    Configuration for application logging
    """

    LOG_LEVEL: str = Field(
        description="Logging level, default to INFO. Set to ERROR for production environments.",
        default="INFO",
    )

    LOG_FOLDER: str = Field(
        description="File path for log output.",
        default="logs",
    )
