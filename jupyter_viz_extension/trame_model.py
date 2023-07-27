import logging
import os
from dataclasses import dataclass, field
from io import FileIO
from pathlib import Path
from socket import socket
from subprocess import Popen
from tempfile import mkstemp
from yaml import safe_load
from traitlets.config import SingletonConfigurable


def _next_open_port() -> int:
    # We let socket determine an available open port
    with socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@dataclass
class TrameAppInstance:
    port: int
    log_dir: str
    logger: FileIO
    process_handle: Popen

    def dump(self) -> dict:
        return {
            "port": self.port,
            "log": self.log_dir,
        }


@dataclass
class TrameApp:
    name: str
    display_name: str
    path: str
    command: str
    working_directory: str = None
    instances: list[TrameAppInstance] = field(default_factory=list)

    def dump(self) -> dict:
        return {
            "name": self.name,
            "displayName": self.display_name,
            "path": self.path,
            "instances": [instance.dump() for instance in self.instances]
        }


class TrameModel(SingletonConfigurable):
    _apps: dict[str, TrameApp]

    def __init__(self, logger: logging.Logger):
        super().__init__()

        self._apps = dict()
        self._log = logger
        self.discover_apps()

    @property
    def apps(self) -> dict[str, TrameApp]:
        return self._apps

    @property
    def app_names(self) -> list[str]:
        return list(self._apps.keys())

    def discover_apps(self):
        # We use JUPYTER_PATH to discover Apps
        paths = os.getenv("JUPYTER_PATH")
        paths = paths.split(os.pathsep) if paths else []
        self._log.info(f"Searching for trame apps in {paths!r}")

        for path in paths:
            path = Path(path) / "trame"
            if not path.is_dir() or not path.exists():
                continue

            for name in path.iterdir():
                self.parse_app_config(name)

    def parse_app_config(self, path):
        # Open Config
        config_file = path / "app.yml"
        if not config_file.exists():
            config_file = path / "app.yaml"

            if not config_file.exists():
                raise AttributeError(f"trame app at {path.resolve()!r} does not have a app.yml file")

        self._log.info(f"Found trame app config at {config_file.resolve()!r}")

        config = safe_load(config_file.read_text())
        self._apps[path.name] = TrameApp(
            name=path.name,
            display_name=config["name"],
            path=str(config_file.resolve()),
            command=config["command"],
            working_directory=config.get("working_directory", None),
        )

    async def launch_trame(self, app_name: str) -> TrameAppInstance:
        config = self._apps[app_name]

        # Determine Parameters
        port = _next_open_port()
        _, log_dir = mkstemp(suffix=".log", text=True)
        logger = FileIO(log_dir, "w")

        self._log.info(f"Starting {app_name} on port {port}, logging to {log_dir}")

        # Prepare Environment
        env = os.environ.copy()
        env["JUVIZ_ARGS"] = f"--port={port} --server"

        # Create Process
        process = Popen(
            config.command, env=env, cwd=config.working_directory,
            shell=True, stdout=logger, stderr=logger, text=True
        )

        # Add Instance
        self._apps[app_name].instances.append(
            instance := TrameAppInstance(port, log_dir, logger, process)
        )

        return instance
