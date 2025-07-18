from fastapi.openapi.utils import get_openapi

from ..beco_app import BecoApp


class OpenAPIExtension:
    """
    Extension to customize the OpenAPI schema to add API key security for Swagger UI.
    """

    def __init__(self):
        self._initialized = False

    def init_app(self, app):
        if self._initialized:
            return

        def custom_openapi():
            openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )

            openapi_schema["components"]["securitySchemes"] = {
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
            openapi_schema["security"] = [{"BearerAuth": []}]
            app.openapi_schema = openapi_schema
            return app.openapi_schema

        app.openapi = custom_openapi
        self._initialized = True


def is_enabled():
    return True


def init_app(app: BecoApp):
    openapi_extension = OpenAPIExtension()
    openapi_extension.init_app(app)
