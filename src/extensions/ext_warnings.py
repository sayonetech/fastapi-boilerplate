from ..beco_app import BecoApp


def init_app(app: BecoApp):
    import warnings

    warnings.simplefilter("ignore", ResourceWarning)
