from ._version import __version__
from .handlers import setup_handlers


def _jupyter_labextension_paths():
    return [{
        "src": "labextension",
        "dest": "jupyter-viz-extension"
    }]


def _jupyter_server_extension_points():
    return [{
        "module": "jupyter_viz_extension"
    }]


def _load_jupyter_server_extension(server_app):
    setup_handlers(server_app.web_app)
    name = "jupyter_viz_extension"
    server_app.log.info(f"Registered {name} server extension")


# For backward compatibility with notebook server
load_jupyter_server_extension = _load_jupyter_server_extension

