from ..beco_app import BecoApp
from ..configs import madcrow_config


def init_app(app: BecoApp):
    from fastapi.middleware.cors import CORSMiddleware

    # Add CORS middleware using configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=madcrow_config.web_api_cors_allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
