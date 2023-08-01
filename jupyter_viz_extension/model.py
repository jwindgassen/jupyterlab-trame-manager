import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from io import FileIO
from jinja2 import Template
from jupyter_server.utils import url_path_join
from pathlib import Path
from socket import socket
from subprocess import Popen
from tempfile import mkstemp, NamedTemporaryFile
from tornado.httpclient import AsyncHTTPClient
from yaml import safe_load

from .cmd import output


def _next_open_port() -> int:
    # We let socket determine an available open port
    with socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@dataclass(kw_only=True)
class ParaViewServer:
    name: str
    account: str
    partition: str
    nodes: int
    time_used: str
    time_limit: str
    state: str
    node_list: str
    connection_address: str

    def dump(self) -> dict:
        return {
            "name": self.name,
            "account": self.account,
            "partition": self.partition,
            "nodes": self.nodes,
            "timeUsed": self.time_used,
            "timeLimit": self.time_limit,
            "state": self.state,
            "connectionAddress": self.connection_address,
        }


@dataclass(kw_only=True)
class TrameAppInstance:
    name: str
    data_directory: str
    port: int
    base_url: str
    log_dir: str
    logger: FileIO
    process_handle: Popen

    def dump(self) -> dict:
        return {
            "name": self.name,
            "dataDirectory": self.data_directory,
            "port": self.port,
            "base_url": self.base_url,
            "log": self.log_dir,
        }


@dataclass(kw_only=True)
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


class Model:
    _apps: dict[str, TrameApp]
    _servers: list[ParaViewServer]

    def __init__(self, logger: logging.Logger, base_url: str):
        super().__init__()

        self._apps = dict()
        self._servers = []
        self._log = logger
        self._base_url = base_url

        self.discover_apps()
        asyncio.run(self.get_running_servers())

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

    async def launch_trame(self, app_name: str, name: str, data_directoy: str) -> TrameAppInstance:
        config = self._apps[app_name]

        # Determine Parameters
        port = _next_open_port()
        _, log_dir = mkstemp(suffix=".log", text=True)
        logger = FileIO(log_dir, "w")

        self._log.info(f"Starting {app_name} on port {port}, logging to {log_dir}")

        # Prepare Environment
        env = os.environ.copy()
        env["JUVIZ_ARGS"] = f"--port={port} --data={data_directoy} --server"

        # Create Process
        process = Popen(
            config.command, env=env, cwd=config.working_directory,
            shell=True, stdout=logger, stderr=logger, text=True
        )

        # Add Instance
        base_url = url_path_join(self._base_url, "proxy", str(port), "/")  # JupyterServerProxy
        instance = TrameAppInstance(
            name=name,
            data_directory=data_directoy,
            port=port,
            base_url=base_url,
            log_dir=log_dir,
            logger=logger,
            process_handle=process
        )
        self._apps[app_name].instances.append(instance)

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
        _, out = await output("squeue", "--me", "--noheader", "--Format='Name,Account,Partition,NumNodes,TimeUsed,TimeLimit,State,NodeList'")

        self._servers = []
        for server in out.splitlines():
            self._log.info(f"Found Server: {server}")
            name, partition, account, nodes, time_used, time_limit, state, *node_list = server.split()

            server = ParaViewServer(
                name=name,
                account=account,
                partition=partition,
                nodes=int(nodes),
                time_used=time_used,
                time_limit=time_limit,
                state=state,
                node_list=node_list,
                connection_address=f"jwb{node_list[4:8]}i.juwels" if state == "RUNNING" else None
            )
            self._servers.append(server)

    async def launch_paraview(self, options):
        self._log.info(f"Launching ParaView with Options {options!r}")

        input_file = Path(__file__).parent / ".." / "share" / "launch_paraview.in"
        template = Template(input_file.read_text())

        # Create a tempfile and write the SLURM Config into it
        with NamedTemporaryFile("w", delete=False) as tmp:
            path = tmp.name
            tmp.write(template.render(options))

        self._log.info(f"Job script in {path!r}")
        return await output("sbatch", path, logger=self._log)

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
