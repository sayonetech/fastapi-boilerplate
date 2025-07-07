# app/extensions/ext_db.py
from fastapi import FastAPI
from sqlmodel import create_engine

from src.configs import madcrow_config


class DBEngine:
    def __init__(self):
        self._engine = None

    def init_app(self, app: FastAPI):
        # TODO: Use correct url for production
        DATABASE_URL = "postgresql+psycopg2://postgres:123456@localhost:5432/madcrow"

        self._engine = create_engine(
            # madcrow_config.DB_URL,
            DATABASE_URL,
            echo=madcrow_config.DEBUG,
        )
        # store engine on app for global access
        app.state.engine = self._engine

    def get_engine(self):
        return self._engine


db_engine = DBEngine()


def init_app(app: FastAPI):
    db_engine.init_app(app)
