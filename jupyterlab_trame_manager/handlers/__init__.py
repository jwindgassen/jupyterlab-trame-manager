from jupyter_server.utils import url_path_join
from jupyter_server.serverapp import ServerWebApplication

from .paraview import ParaViewHandler
from .trame import TrameHandler, TrameActionHandler
from .user import UserHandler


def setup_handlers(web_app: ServerWebApplication, model):
    base_url = url_path_join(web_app.settings["base_url"], "trame-manager")
    web_app.add_handlers(".*$", [
        (url_path_join(base_url, "paraview"),        ParaViewHandler,    dict(model=model)),
        (url_path_join(base_url, "trame"),           TrameHandler,       dict(model=model)),
        (url_path_join(base_url, "trame", r"(\w+)"), TrameActionHandler, dict(model=model)),
        (url_path_join(base_url, "user"),            UserHandler,        dict(model=model)),
    ])
