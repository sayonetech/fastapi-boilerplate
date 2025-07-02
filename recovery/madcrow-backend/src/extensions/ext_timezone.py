import os
import time

from ..beco_app import BecoApp


def init_app(app: BecoApp):
    os.environ["TZ"] = "UTC"
    if hasattr(time, "tzset"):
        time.tzset()
