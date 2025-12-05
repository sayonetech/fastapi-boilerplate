from .db_config import DatabaseConfig
from .http_config import HttpConfig
from .logging_config import LoggingConfig
from .redis_config import RedisConfig
from .security_config import SecurityConfig


class EnvironmentConfig(
    # place the configs in alphabet order
    HttpConfig,
    LoggingConfig,
    RedisConfig,
    SecurityConfig,
    DatabaseConfig,
):
    pass
