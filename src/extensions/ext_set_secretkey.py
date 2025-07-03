from ..beco_app import BecoApp
from ..configs import madcrow_config


def init_app(app: BecoApp):
    app.state.secret_key = madcrow_config.SECRET_KEY
