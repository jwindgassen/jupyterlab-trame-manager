import os
from abc import ABC, abstractmethod
from io import FileIO
from jupyter_server.serverapp import ServerApp
from pathlib import Path
from secrets import token_urlsafe, token_hex
from socket import socket
from subprocess import Popen
from tempfile import mkstemp
from yaml import safe_load

from ..types import *
from ..proxy import make_trame_proxy_handler


class Configuration(ABC):
    def __init__(self, logger):
        self._logger = logger

    @property
    def log(self):
        return self._logger

    @staticmethod
    def get_open_port() -> int:
        # We let socket determine an available open port
        with socket() as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def discover_apps(self) -> list[TrameApp]:
        # We use JUPYTER_PATH to discover Apps
        paths = os.getenv("JUPYTER_PATH")
        paths = paths.split(os.pathsep) if paths else []
        self.log.info(f"Searching for trame apps in {paths!r}")

        apps = []
        for path in paths:
            path = Path(path) / "trame"
            if not path.is_dir() or not path.exists():
                continue

            for name in path.iterdir():
                app = self.parse_app_config(name)
                apps.append(app)

        return apps

    def parse_app_config(self, path) -> TrameApp:
        # Open Config
        config_file = path / "app.yml"
        if not config_file.exists():
            config_file = path / "app.yaml"

            if not config_file.exists():
                raise AttributeError(f"trame app at {path.resolve()!r} does not have a app.yml file")

        self.log.info(f"Found trame app config at {config_file.resolve()!r}")

        config = safe_load(config_file.read_text())
        return TrameApp(
            name=path.name,
            display_name=config["name"],
            path=str(config_file.resolve()),
            command=config["command"],
            working_directory=config.get("working_directory", None),
        )

    def generate_trame_parameters(self, app: TrameApp) -> dict:
        # UUID
        uuid = token_hex(8)

        # Port
        port = self.get_open_port()

        # Log-file
        _, log_dir = mkstemp(suffix=".log", text=True)
        logger = FileIO(log_dir, "w")

        # authKey
        auth_key = token_urlsafe(32)

        # Write authKey to tempfile
        tempfile, auth_key_file = mkstemp(text=True)
        with open(tempfile, "w") as file:
            file.write(auth_key)

        self.log.info(f"{uuid=}, {port=}, {log_dir=}, {auth_key_file=}")
        return {
            "uuid": uuid,
            "port": port,
            "log_dir": log_dir,
            "logger": logger,
            "auth_key": auth_key,
            "auth_key_file": auth_key_file,
        }

    def generate_trame_env(self, instance: TrameAppInstance) -> dict:
        env = os.environ.copy()
        env["JUVIZ_ARGS"] = (f"--port={instance.port} "
                             f"--data={instance.data_directory} "
                             f"--authKeyFile={instance.auth_key_file} "
                             f"--server")
        return env

    def route_trame(self, instance: TrameAppInstance, server_app: ServerApp) -> str:
        base_url, rule = make_trame_proxy_handler(instance, server_app.base_url)
        server_app.web_app.add_handlers('.*', [rule])
        return base_url

    async def launch_trame(self, app: TrameApp, server_app, **options) -> TrameAppInstance:
        parameters = self.generate_trame_parameters(app)
        self.log.info(f"Starting {app.name}")

        instance = TrameAppInstance(
            **options,
            **parameters,
            process_handle=None,
            base_url="",
        )

        # env and handler
        env = self.generate_trame_env(instance)
        instance.base_url = self.route_trame(instance, server_app)

        # Create Process
        process = Popen(
            app.command, env=env, cwd=app.working_directory,
            shell=True, stdout=instance.logger, stderr=instance.logger, text=True
        )
        instance.process_handle = process

        return instance

    @abstractmethod
    async def get_running_servers(self) -> list[ParaViewServer]:
        pass

    @abstractmethod
    async def launch_paraview(self, options: dict) -> tuple[int, str]:
        pass

    @abstractmethod
    async def get_user_data(self) -> UserData:
        pass
