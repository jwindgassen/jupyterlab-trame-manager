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
from pydantic import BaseModel, Field, ConfigDict, alias_generators, types, networks
from pydantic.functional_validators import BeforeValidator
from typing_extensions import Annotated

from .proxy import make_trame_proxy_handler


__all__ = [
    "Configuration",
    "UserData", "TrameApp", "TrameLaunchOptions", "TrameInstance", "ParaViewLaunchOptions", "ParaViewInstance",
    "ParentModel", "DirectoryPath", "FilePath"
]


# Ensure, that paths have the tilde expanded and are fully resolved, to give a nice, complete path when dumping
def _expand_and_resolve_path(path: Path | str) -> Path:
    return Path(path).expanduser().resolve()


# Apply Resolve before the Pydantic Validation
DirectoryPath = Annotated[types.DirectoryPath, BeforeValidator(_expand_and_resolve_path)]
FilePath = Annotated[types.FilePath, BeforeValidator(_expand_and_resolve_path)]


class ParentModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=alias_generators.to_camel,
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )

class TrameLaunchOptions(ParentModel):
    """
    Trame App Launch Options, specified in the launch dialog.

    ToDo: Let App decide what fields should be specified by the User (e.g. via app.yml)
    """
    name: str
    data_directory: DirectoryPath

class TrameInstance(TrameLaunchOptions):
    """
    Data related to a running Instance of a trame App.

    ToDo: Let App decide what fields should be specified by the User (e.g. via app.yml)
    """
    uuid: str = Field(default_factory=lambda: token_hex(8))
    port: int
    base_url: networks.HttpUrl | None
    log_file: FilePath = Field(alias="log")

    auth_key: str = Field(exclude=True)
    auth_key_file: FilePath = Field(exclude=True)
    logger: FileIO = Field(exclude=True)
    process_handle: Popen | None = Field(exclude=True)


class TrameApp(ParentModel):
    """
    Information about one specific trame App, like the launch command and its running instances.
    """
    name: str  # Internal name
    path: FilePath  # Path to the app.yml

    display_name: str
    command: str = Field(exclude=True)
    working_directory: DirectoryPath | None = Field(exclude=True)

    instances: list[TrameInstance] = []


class UserData(ParentModel, extra="allow"):
    """
    Store data about the user.
    You can add extra information for your Configuration if required.
    """
    user: str
    home: DirectoryPath = "~"
    accounts: list[str]
    partitions: list[str]


class ParaViewLaunchOptions(ParentModel, extra="allow"):
    """
    ParaView Server options, specified in the launch dialog.
    ToDo: Other systems might need other options
    """
    name: str
    account: str
    partition: str
    nodes: int
    time_limit: str


class ParaViewInstance(ParaViewLaunchOptions, extra="allow"):
    """
    Store data about a running ParaView Server.
    You can add extra information for your Configuration if required.
    """
    time_used: str
    state: str
    connection_address: str = Field(exclude=True)


class Configuration(ABC):
    """
    The Configuration class allows users to customize the behaviour of the Backend. By creating a custom
    Configuration class, you can change how ParaView is launched, how trame instances are launched and how to load the
    config file for a trame app. See the methods here or the predefined configuration for reference.
    The Configuration is determined at runtime using the "TRAME_MANAGER_CONFIGURATION" environment variable.
    """

    def __init__(self, logger):
        self._logger = logger

    @property
    def log(self):
        """ Logger property """
        return self._logger

    @staticmethod
    def get_open_port() -> int:
        """ Query an open socket on the machine """

        # We let socket determine an available open port
        with socket() as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def discover_apps(self) -> list[TrameApp]:
        """
        Search the system for trame apps that can be launched.
        The default behavious will rely on the `JUPYTER_PATH`environment variable, where trame apps will be found in
        `trame/<app_name> directories`.

        @return: A list wich all the found trame apps
        """
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
        """
        Parse the app.yml file of a trame app. A default config file has the following values:

        - name: The display name of the app to be shown in the UI
        - command: The shell command that will be executed to lauch an instance for this trame app
            This command must append the $TRAME_INSTANCE_ARGS environment variable to the python script, which provides
            some information for trame. See L{Configuration.generate_trame_env} for the generation of the variable.
        - working_directore: Optional, location here I{command} will be executed.

        @param path: The path to the app folder, i.e., `share/jupyter/trame/my-app/`
        @return: The parsed app information for the app
        """
        # Open Config
        config_file = path / "app.yml"
        if not config_file.exists():
            config_file = path / "app.yaml"

            if not config_file.exists():
                raise AttributeError(f"trame app at {path.resolve()!r} does not have a app.yml file")

        self.log.info(f"Found trame app config at {config_file.resolve()!r}")

        config = safe_load(config_file.read_text())
        config["display_name"] = config.pop("name")
        return TrameApp(name=path.name, path=config_file, **config)

    def generate_trame_parameters(self, app: TrameApp) -> dict:
        """
        Some of the parameters for a launched trame app is generated on the server by this configuration. The parameters
        generated by this function are directly passed to the constructor of L{TrameAppInstance}.

        By default, this function generated a UUID, the port to run on, a logger where the outputs of the app are logged
        to, and a tempfile where the authentication key is stored.

        @param app: A reference to the trame app that should be launched
        @return: A dict with the generated parameters
        """

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

        self.log.info(f"{port=}, {log_dir=}, {auth_key_file=}")
        return {
            "port": port,
            "log_file": log_dir,
            "logger": logger,
            "auth_key": auth_key,
            "auth_key_file": auth_key_file,
        }

    def generate_trame_env(self, instance: TrameInstance) -> dict:
        """
        Generated the environment used by the trame instance. This environment contains the $TRAME_INSTANCE_ARGS variable, that
        passes information, e.g., the port, to trame.

        @param instance: A reference to the trame instance that will be launched
        @return: The generated environment
        """
        env = os.environ.copy()
        env["TRAME_INSTANCE_ARGS"] = (f"--port={instance.port} "
                                      f"--data=\"{instance.data_directory}\" "
                                      f"--authKeyFile=\"{instance.auth_key_file}\" "
                                      f"--server")

        return env

    def route_trame(self, instance: TrameInstance, server_app: ServerApp) -> str:
        """
        After trame has been lauched, it must be routed to the user and made accessible by the browser. This
        implementation relies on L{jupyter_server_proxy.NamedLocalProxyHandler}, that will be registered to
        `/trame/<UUID>/` on the server.

        @param instance: The launched trame instance
        @param server_app: A reference to the server of this JupyterLab
        @return: The base_url of the trame instance that will be opened when the user click on this instance in the lab
        """
        base_url, rule = make_trame_proxy_handler(instance, server_app.base_url)
        server_app.web_app.add_handlers('.*', [rule])
        return base_url

    async def launch_trame(self, app: TrameApp, options: TrameLaunchOptions, server_app) -> TrameInstance:
        """
        Launch a new instance of the given trame app.

        @param app: The trame app that should be launched.
        @param options: The options for this instance that were entered by the user in the launch dialog.
        @param server_app: A reference to the server of JupyterLab, might be required to route trame.
        @return: The launched trame instance.
        """
        parameters = self.generate_trame_parameters(app)
        self.log.info(f"Starting {app.name}")

        instance = TrameInstance(
            **options.model_dump(),
            **parameters,
            process_handle=None,
            base_url=None,
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
    async def get_running_servers(self) -> list[ParaViewInstance]:
        """
        Get the list of currently running ParaView Servers that were launched via the extension. This information can,
        e.g., be fetched from the job scheduler.

        @return: A list of all ParaView Servers
        """
        pass

    @abstractmethod
    async def launch_paraview(self, options: ParaViewLaunchOptions) -> tuple[int, str]:
        """
        Lauch a new ParaView Server. This server should be lauched such that L{Configuration.get_running_servers} is
        able to retrieve the information persistently, even after JupyterLab has been restarted.

        @param options: The options for this instance.
        @return: The status of the launch command. This include the return code and an error message. The message will
            be displayed in the UI, as an error when the return code is != 0
        """
        pass

    @abstractmethod
    async def get_user_data(self) -> UserData:
        """
        Query information about the user. This includes:
        - The name of the user
        - The available accounts and partitions available when launching a ParaView Server
        - The path to the home directory, served as the default data directory for trame apps

        @return: The retrieved information about the user
        """
        pass
