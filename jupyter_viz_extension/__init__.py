from jupyter_server.serverapp import ServerApp
from jupyter_server.utils import url_path_join

from ._version import __version__
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
    model = Model(server_app.log, server_app.base_url)
    setup_handlers(server_app.web_app, model)

    name = "jupyter_viz_extension"
    server_app.log.info(f"Registered {name} server extension")


# For backward compatibility with notebook server
load_jupyter_server_extension = _load_jupyter_server_extension

