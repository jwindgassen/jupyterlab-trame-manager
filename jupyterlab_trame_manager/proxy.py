from jupyter_server_proxy.handlers import NamedLocalProxyHandler
from jupyter_server.utils import url_path_join
from typing import Any

from .types import TrameAppInstance


def make_trame_proxy_handler(instance: TrameAppInstance, base_url: str) -> tuple[str, tuple[str, Any]]:
    """
    Create a JupyterServerProxy handler. This handler will append the authentication key to the URL whenever an
    authenticated user tries to access the root of a trame app so trame/wslink can encrypt the traffic on the sockets

    @param instance: The trame instance for which to create the proxy
    @param base_url: The base URL of the JupyterLab Server
    @return: The URL for the proxy handler (<base_url>/trame/<uuid>/) and the parameters for creaing a handler
    """
    def _mappath(path):
        # Append authKey to URL if we are at the base-url
        if path in ("/", "/index.html"):
            path += f"?secret={instance.auth_key}"
            path += "&disableSharedArrayBuffer=1"  # Disable COI

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
