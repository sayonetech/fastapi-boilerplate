from ..beco_app import BecoApp


def init_app(app: BecoApp):
    from fastapi.middleware.cors import CORSMiddleware

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
