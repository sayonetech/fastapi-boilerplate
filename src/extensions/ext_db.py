from fastapi import FastAPI
from sqlmodel import create_engine

from src.configs import madcrow_config


class DBEngine:
    def __init__(self):
        self._engine = None

    def init_app(self, app: FastAPI):
        # Use the DatabaseConfig from madcrow_config
        db_config = madcrow_config

        # Create database URL using the configuration
        database_url = db_config.sqlalchemy_database_uri
        engine_options = db_config.sqlalchemy_engine_options

        self._engine = create_engine(  # type: ignore
            database_url,
            echo=db_config.SQLALCHEMY_ECHO,
            **engine_options,
        )
        # store engine on app for global access
        app.state.engine = self._engine

    def get_engine(self):
        return self._engine


db_engine = DBEngine()


def init_app(app: FastAPI):
    db_engine.init_app(app)
