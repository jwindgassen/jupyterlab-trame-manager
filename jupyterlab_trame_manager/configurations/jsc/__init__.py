import asyncio
import os
from json import loads
from jinja2 import Template
from pathlib import Path
from re import findall
from tempfile import mkdtemp

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
                              "--noheader", "--Format='Name:;,Account:;,Partition:;,NumNodes:;,TimeUsed:;,TimeLimit:;,State:;,NodeList'")

        servers = []
        for server in out.splitlines():
            self.log.info(f"Found Server: {server}")
            name, partition, account, nodes, time_used, time_limit, state, node_list = server.split(";")

            root_node = findall(r"jwb\[?(\d{4})", node_list)[0]
            self.log.info(f"Root Node: {root_node}")

            server = ParaViewServer(
                name=name,
                account=account,
                partition=partition,
                nodes=int(nodes),
                time_used=time_used,
                time_limit=time_limit,
                state=state,
                node_list=node_list,
                connection_address=f"jwb{root_node}i.juwels" if state == "RUNNING" else None
            )
            servers.append(server)

        return servers

    async def launch_paraview(self, options: dict) -> tuple[int, str]:
        self.log.info(f"Launching ParaView with Options {options!r}")

        # Get the input file, depending on the selected partition
        if options["partition"] in ("booster", "develbooster"):
            input_file = Path(__file__).parent / "paraview_juwelsbooster.in"
        else:
            raise ValueError(f"Unkown Partition: {options['partition']}")

        # Create a tempfile and write the SLURM Config and log files into it
        temp_dir = Path(os.getenv("SCRATCH"), "trame-manager-jobs")
        temp_dir.mkdir(parents=True, exist_ok=True)

        job_dir = Path(mkdtemp(prefix=os.getenv("USER"), dir=temp_dir))
        options["stdout"] = (job_dir / "stdout").resolve()
        options["stderr"] = (job_dir / "stderr").resolve()

        template = Template(input_file.read_text())
        with open(job_path := (job_dir / "paraview.job").resolve(), "w") as job_file:
            job_file.write(template.render(options))

        self.log.info(f"Job files can be found in {str(job_dir)!r}")
        return await output("sbatch", str(job_path), logger=self.log)

    async def get_user_data(self) -> UserData:
        username, accounts, partitions = await asyncio.gather(
            output("whoami"),
            _get_accounts(),
            _get_partitions()
        )
        home = os.path.expanduser("~")

        return UserData(username[1], home, accounts, partitions)
