from jupyter_server_proxy.handlers import NamedLocalProxyHandler
from jupyter_server.utils import url_path_join

from .types import TrameAppInstance


def make_trame_proxy_handler(instance: TrameAppInstance, base_url: str):
    def _mappath(path):
        # Append authKey to URL if we are at the base-url
        if path in ("/", "/index.html"):
            path += f"?secret={instance.auth_key}"

        return path

    class _Proxy(NamedLocalProxyHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.port = instance.port
            self.mappath = _mappath
            self.proxy_base = url_path_join("trame", instance.uuid)

            self.absolute_url = False
            self.unix_socket = None
            self.rewrite_response = tuple()

    base_url = url_path_join(base_url, "trame", instance.uuid, "/")
    rule_url = url_path_join(base_url, r"(.*)")

    return base_url, (rule_url, _Proxy)
