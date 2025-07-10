from typing import Annotated

from pydantic import AliasChoices, Field, PositiveFloat, PositiveInt, computed_field
from pydantic_settings import BaseSettings


class HttpConfig(BaseSettings):
    """
    HTTP-related configurations for the application
    """

    API_COMPRESSION_ENABLED: bool = Field(
        description="Enable or disable gzip compression for HTTP responses",
        default=False,
    )

    inner_WEB_API_CORS_ALLOW_ORIGINS: str = Field(
        description="Comma-separated list of allowed origins for CORS in the web API",
        validation_alias=AliasChoices("WEB_API_CORS_ALLOW_ORIGINS"),
        default="*",
    )

    @computed_field
    @property
    def web_api_cors_allow_origins(self) -> list[str]:
        return self.inner_WEB_API_CORS_ALLOW_ORIGINS.split(",")

    HTTP_REQUEST_MAX_CONNECT_TIMEOUT: Annotated[
        PositiveInt,
        Field(ge=10, description="Maximum connection timeout in seconds for HTTP requests"),
    ] = 10

    HTTP_REQUEST_MAX_READ_TIMEOUT: Annotated[
        PositiveInt,
        Field(ge=60, description="Maximum read timeout in seconds for HTTP requests"),
    ] = 60

    HTTP_REQUEST_MAX_WRITE_TIMEOUT: Annotated[
        PositiveInt,
        Field(ge=10, description="Maximum write timeout in seconds for HTTP requests"),
    ] = 20

    HTTP_REQUEST_NODE_MAX_BINARY_SIZE: PositiveInt = Field(
        description="Maximum allowed size in bytes for binary data in HTTP requests",
        default=10 * 1024 * 1024,
    )

    HTTP_REQUEST_NODE_MAX_TEXT_SIZE: PositiveInt = Field(
        description="Maximum allowed size in bytes for text data in HTTP requests",
        default=1 * 1024 * 1024,
    )

    SSRF_DEFAULT_MAX_RETRIES: PositiveInt = Field(
        description="Maximum number of retries for network requests (SSRF)",
        default=3,
    )

    SSRF_PROXY_ALL_URL: str | None = Field(
        description="Proxy URL for HTTP or HTTPS requests to prevent Server-Side Request Forgery (SSRF)",
        default=None,
    )

    SSRF_PROXY_HTTP_URL: str | None = Field(
        description="Proxy URL for HTTP requests to prevent Server-Side Request Forgery (SSRF)",
        default=None,
    )

    SSRF_PROXY_HTTPS_URL: str | None = Field(
        description="Proxy URL for HTTPS requests to prevent Server-Side Request Forgery (SSRF)",
        default=None,
    )

    SSRF_DEFAULT_TIME_OUT: PositiveFloat = Field(
        description="The default timeout period used for network requests (SSRF)",
        default=5,
    )

    SSRF_DEFAULT_CONNECT_TIME_OUT: PositiveFloat = Field(
        description="The default connect timeout period used for network requests (SSRF)",
        default=5,
    )

    SSRF_DEFAULT_READ_TIME_OUT: PositiveFloat = Field(
        description="The default read timeout period used for network requests (SSRF)",
        default=5,
    )

    SSRF_DEFAULT_WRITE_TIME_OUT: PositiveFloat = Field(
        description="The default write timeout period used for network requests (SSRF)",
        default=5,
    )

    RESPECT_XFORWARD_HEADERS_ENABLED: bool = Field(
        description="Enable or disable the X-Forwarded-For Proxy Fix middleware from Werkzeug"
        " to respect X-* headers to redirect clients",
        default=False,
    )
