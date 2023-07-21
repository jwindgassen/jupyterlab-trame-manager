import json
import os
import socket
import yaml
from subprocess import Popen
from pathlib import Path

from jupyter_server.base.handlers import APIHandler
from tornado.web import authenticated


trame_apps = dict()
processes = []


def _next_open_port() -> int:
    # We let socket determine an available open port
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def _discover_apps():
    # We use JUPYTER_PATH to discover Apps
    paths = os.getenv("JUPYTER_PATH")
    paths = paths.split(os.pathsep) if paths else []
    print(f"Searching for trame apps in {paths!r}")

    for path in paths:
        path = Path(path) / "trame"
        for short_name in path.iterdir():
            # Open Config
            config_file = short_name / "app.yml"
            if not config_file.exists():
                raise AttributeError(f"trame app at {short_name.resolve()} does not have a app.yml file")

            print(f"Found config at {config_file.resolve()!r}")

            config = yaml.safe_load(config_file.read_text())
            config["path"] = short_name.resolve()

            trame_apps[short_name.name] = config

        
async def _launch_trame(app_name: str) -> int:
    config = trame_apps[app_name]

    # Determine Port
    port = _next_open_port()

    # Prepare Environment
    env = os.environ.copy()
    env["JUVIZ_ARGS"] = f"--port={port} --server"

    print(f"Starting {app_name} on port {port}")
    process = Popen(config["command"], shell=True, env=env, cwd=config.get("working_directory", None))
    processes.append(process)

    return port


class TrameHandler(APIHandler):
    @authenticated
    async def get(self):
        if not trame_apps:
            _discover_apps()

        print(trame_apps)

        await self.finish(json.dumps([
            {
                "name": name,
                "displayName": config["name"],
                "path": str(config["path"].resolve()),
                "instances": []
            }
            for name, config in trame_apps.items()
        ]))
    
    @authenticated
    async def post(self):
        app_name = self.get_argument("app_name", "juviz")
        
        print(f"Launching new trame instance '{app_name}'")

        try:
            port = await _launch_trame(app_name)
            self.set_status(200)
            await self.finish({"port": port})
            
        except Exception as e:
            print(e)
            self.set_status(400)
            await self.finish(str(e))
