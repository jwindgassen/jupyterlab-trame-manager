import asyncio
import json
import logging
import os
from importlib import import_module
from jupyter_server.serverapp import ServerApp
from jupyter_server.utils import url_path_join
from socket import socket
from tornado.httpclient import AsyncHTTPClient

from .configurations import Configuration
from .types import *


def _next_open_port() -> int:
    # We let socket determine an available open port
    with socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


class Model:
    _configuration: Configuration
    _apps: dict[str, TrameApp]
    _servers: list[ParaViewServer]

    def __init__(self, server_app: ServerApp):
        super().__init__()

        self._apps = dict()
        self._servers = []
        self._server_app = server_app

        # Get Configuration
        conf_name = os.getenv("JUVIZ_CONFIGURATION")
        if conf_name is None:
            raise EnvironmentError("'JUVIZ_CONFIGURATION' not set!")

        module = import_module(f"jupyter_viz_extension.configurations.{conf_name}")
        cls = [
            cls for cls in module.__dict__.values()
            if isinstance(cls, type) and issubclass(cls, Configuration) and cls != Configuration
        ][0]
        self._log.info(f"Found Configuration class {cls.__name__!r}")

        self._configuration = cls(self._log)

        # Discover Apps and Servers
        self.discover_apps()
        asyncio.run(self.get_running_servers())

    @property
    def _log(self) -> logging.Logger:
        return self._server_app.log

    async def get_user_data(self) -> UserData:
        return await self._configuration.get_user_data()

    ########################################################
    #
    #   Trame
    #
    ########################################################

    @property
    def apps(self) -> dict[str, TrameApp]:
        return self._apps

    @property
    def app_names(self) -> list[str]:
        return list(self._apps.keys())

    def discover_apps(self):
        apps = self._configuration.discover_apps()
        app_names = [app.name for app in apps]

        self._apps = dict(zip(app_names, apps))

    async def launch_trame(self, app_name: str, **options) -> TrameAppInstance:
        app = self.apps[app_name]

        instance = await self._configuration.launch_trame(app, self._server_app, **options)
        app.instances.append(instance)

        return instance

    ########################################################
    #
    #   ParaView
    #
    ########################################################

    @property
    def servers(self):
        return self._servers

    async def get_running_servers(self):
        self._servers = await self._configuration.get_running_servers()

    async def launch_paraview(self, options):
        return await self._configuration.launch_paraview(options)

    ########################################################
    #
    #   Connections
    #
    ########################################################

    async def connect_to_backend(self, app_name: str, instance_name: str, server_name):
        instance = [app for app in self.apps[app_name].instances if app.name == instance_name][0]
        server = [server for server in self.servers if server.name == server_name][0]

        juviz_url = url_path_join(f"http://localhost:{instance.port}",  "juviz")  # ToDo: Also use JSP?
        self._log.info(f"JuViz Endpoint: {juviz_url!r}")

        client = AsyncHTTPClient()
        await client.fetch(juviz_url, method="POST", body=json.dumps({
            "action": "connect",
            "url": server.connection_address,
            "port": 11111,
        }))

        return dict(url=server.connection_address)

    async def disconnect(self, app_name, instance_name):
        instance = [app for app in self.apps[app_name].instances if app.name == instance_name][0]
        juviz_url = url_path_join(f"http://localhost:{instance.port}",  "juviz")

        client = AsyncHTTPClient()
        await client.fetch(juviz_url, method="POST", body=json.dumps({
            "action": "disconnect",
        }))
