from .auth import auth_router
from .database_example import database_example_router
from .health import health_router
from .profile import profile_router
from .redis_example import redis_example_router
from .security import security_router

__all__ = [
    "auth_router",
    "database_example_router",
    "health_router",
    "profile_router",
    "redis_example_router",
    "security_router",
]
