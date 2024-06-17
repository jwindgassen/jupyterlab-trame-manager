from jupyter_server.serverapp import ServerApp
try:
    from ._version import __version__
except ImportError:
    # Fallback when using the package in dev mode without installing
    # in editable mode with pip. It is highly recommended to install
    # the package from a stable release or in editable mode: https://pip.pypa.io/en/stable/topics/local-project-installs/#editable-installs
    import warnings
    warnings.warn("Importing 'jupyter_viz_extension' outside a proper installation.")
    __version__ = "dev"
from .handlers import setup_handlers
from .model import Model


def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "jupyter-viz-extension"
    }]


def _jupyter_server_extension_points():
    return [{
        "module": "jupyter_viz_extension"
    }]


def _load_jupyter_server_extension(server_app: ServerApp):
    model = Model(server_app)
    setup_handlers(server_app.web_app, model)

    name = "jupyter_viz_extension"
    server_app.log.info(f"Registered {name} server extension")
