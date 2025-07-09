import os
from datetime import UTC, datetime

from pydantic import Field, PositiveInt
from pydantic_settings import BaseSettings


class LoggingConfig(BaseSettings):
    """
    Configuration for application logging
    """

    LOG_LEVEL: str = Field(
        description="Logging level, default to INFO. Set to ERROR for production environments.",
        default="INFO",
    )

    LOG_FOLDER: str | None = Field(
        description="File path for log output.",
        default=None,
    )

    LOG_FILE_MAX_SIZE: PositiveInt = Field(
        description="Maximum file size for file rotation retention, the unit is megabytes (MB)",
        default=20,
    )

    LOG_FILE_BACKUP_COUNT: PositiveInt = Field(
        description="Maximum file backup count file rotation retention",
        default=5,
    )

    LOG_FORMAT: str = Field(
        description="Format string for log messages",
        default="%(asctime)s.%(msecs)03d %(levelname)s [%(threadName)s] [%(filename)s:%(lineno)d] - %(message)s",
    )

    LOG_DATEFORMAT: str | None = Field(
        description="Date format string for log timestamps",
        default=None,
    )

    LOG_TZ: str | None = Field(
        description="Timezone for log timestamps (e.g., 'America/New_York')",
        default="UTC",
    )

    def get_dated_log_file(self) -> str | None:
        """Generate a log filename with the current date appended."""
        if not self.LOG_FOLDER:
            return None

        log_date = datetime.now(UTC).strftime("%d-%m-%Y")
        return os.path.join(self.LOG_FOLDER, f"madcrow-backend-{log_date}.log")
