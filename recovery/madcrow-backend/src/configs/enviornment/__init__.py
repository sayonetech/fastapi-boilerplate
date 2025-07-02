from .http_config import HttpConfig
from .logging_config import LoggingConfig
from .redis_config import RedisConfig
from .security_config import SecurityConfig


class EnviornmentConfig(
    # place the configs in alphabet order
    HttpConfig,
    LoggingConfig,
    RedisConfig,
    SecurityConfig,
):
    pass
