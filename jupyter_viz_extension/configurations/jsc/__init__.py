import asyncio
import os
from json import loads
from jinja2 import Template
from pathlib import Path
from tempfile import NamedTemporaryFile

from .. import Configuration
from ...cmd import output
from ...types import *


async def _get_accounts():
    _, out = await output("jutil", "user", "projects", "--format='json'")
    return [group["unixgroup"] for group in loads(out)] if out else []


async def _get_partitions():
    return ["booster", "develbooster"]


class JscConfiguration(Configuration):
    async def get_running_servers(self) -> list[ParaViewServer]:
        _, out = await output("squeue", "--me",
                              "--noheader", "--Format='Name,Account,Partition,NumNodes,TimeUsed,TimeLimit,State,NodeList'")

        servers = []
        for server in out.splitlines():
            self.log.info(f"Found Server: {server}")
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
            servers.append(server)

        return servers

    async def launch_paraview(self, options) -> tuple[int, str]:
        self.log.info(f"Launching ParaView with Options {options!r}")

        # Get the input file, depending on the selected partition
        if options.partition in ("booster", "develbooster"):
            input_file = Path(__file__).parent / "paraview_juwelsbooster.in"
        else:
            raise ValueError(f"Unkown Partition: {options.partition}")

        # Create a tempfile and write the SLURM Config into it
        template = Template(input_file.read_text())
        with NamedTemporaryFile("w", delete=False) as tmp:
            path = tmp.name
            tmp.write(template.render(options))

        self.log.info(f"Job script in {path!r}")
        return await output("sbatch", path, logger=self.log)

    async def get_user_data(self) -> UserData:
        username, accounts, partitions = await asyncio.gather(
            output("whoami"),
            _get_accounts(),
            _get_partitions()
        )
        home = os.path.expanduser("~")

        return UserData(username[1], home, accounts, partitions)