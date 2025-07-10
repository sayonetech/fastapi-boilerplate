from fastapi import APIRouter


class BaseRouter(APIRouter):
    def __init__(self, *, prefix: str = "", tags: list[str] | None = None, dependencies=None):
        full_prefix = f"/api{prefix}" if not prefix.startswith("/api") else prefix
        super().__init__(prefix=full_prefix, tags=tags or [], dependencies=dependencies or [])
