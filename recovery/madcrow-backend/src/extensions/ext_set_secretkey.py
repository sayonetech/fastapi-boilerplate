from ..beco_app import BecoApp
from ..configs import mcp_agent_config


def init_app(app: BecoApp):
    app.state.secret_key = mcp_agent_config.SECRET_KEY
