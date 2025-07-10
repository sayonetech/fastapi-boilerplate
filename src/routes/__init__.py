import importlib
import pkgutil

from src.routes.base_router import BaseRouter

from ..beco_app import BecoApp


def register_routes(app: BecoApp) -> None:
    # Auto-Discovery of Routers
    for version in ["v1"]:
        package = f"src.routes.{version}"
        path = __import__(package, fromlist=[""]).__path__[0]
        for _, module_name, _ in pkgutil.iter_modules([path]):
            if module_name.startswith("__"):
                continue
            module = importlib.import_module(f"{package}.{module_name}")
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, BaseRouter):
                    app.include_router(attr)