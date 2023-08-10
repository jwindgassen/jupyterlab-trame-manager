import os
from abc import ABC, abstractmethod
from io import FileIO
from jupyter_server.utils import url_path_join
from pathlib import Path
from socket import socket
from subprocess import Popen
from tempfile import mkstemp
from yaml import safe_load

from ..types import *


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

    async def launch_trame(self, app: TrameApp, name: str, data_directoy: str, base_url: str) -> TrameAppInstance:
        # Determine Parameters
        port = self.get_open_port()
        _, log_dir = mkstemp(suffix=".log", text=True)
        logger = FileIO(log_dir, "w")

        self.log.info(f"Starting {app.name} on port {port}, logging to {log_dir}")

        # Prepare Environment
        env = os.environ.copy()
        env["JUVIZ_ARGS"] = f"--port={port} --data={data_directoy} --server"

        # Create Process
        process = Popen(
            app.command, env=env, cwd=app.working_directory,
            shell=True, stdout=logger, stderr=logger, text=True
        )

        # Add Instance
        base_url = url_path_join(base_url, "proxy", str(port), "/")  # JupyterServerProxy
        instance = TrameAppInstance(
            name=name,
            data_directory=data_directoy,
            port=port,
            base_url=base_url,
            log_dir=log_dir,
            logger=logger,
            process_handle=process
        )

        return instance

    @abstractmethod
    async def get_running_servers(self) -> list[ParaViewServer]:
        pass

    @abstractmethod
    async def launch_paraview(self, options) -> tuple[int, str]:
        pass

    @abstractmethod
    async def get_user_data(self) -> UserData:
        pass
