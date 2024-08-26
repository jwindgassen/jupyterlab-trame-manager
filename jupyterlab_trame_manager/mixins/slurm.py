from abc import ABC
from jinja2 import Template
from pathlib import Path
from re import findall
from tempfile import mkdtemp
import os
from ..configuration import Configuration, ParaViewLaunchOptions, ParaViewInstance
from ..cmd import output


class SlurmMixin(Configuration, ABC):
    """
    Configuration Mixin class for managing ParaView Servers via SLURM. This will
    """

    # The Path to the Jinja2 Template used to instantiate the job script
    job_script_template: Path

    # The directory, where new temporary folders for the jobs should be created
    temp_dir: Path

    # A RegEx to extract the root node from the NodeList
    node_name_regex: str

    # A templated string used to generated the connection address of the ParaView Server
    server_address: str

    async def get_running_servers(self) -> list[ParaViewInstance]:
        _, out = await output(
            "squeue",
            "--me", "--noheader",
            "--Format='Name:;,Account:;,Partition:;,NumNodes:;,TimeUsed:;,TimeLimit:;,State:;,NodeList'"
        )

        servers = []
        for server in out.splitlines():
            self.log.info(f"Found Server: {server}")
            name, partition, account, nodes, time_used, time_limit, state, node_list = server.split(";")

            root_node = findall(self.node_name_regex, node_list)[0]
            self.log.info(f"Root Node: {root_node}")

            server = ParaViewInstance(
                name=name,
                account=account,
                partition=partition,
                nodes=int(nodes),
                time_used=time_used,
                time_limit=time_limit,
                state=state,
                connection_address="",
                # Extra Args
                node_list=node_list,
                root_node=root_node,
            )
            server.connection_address = self.server_address % server.model_dump()
            servers.append(server)

        return servers

    async def launch_paraview(self, options: ParaViewLaunchOptions) -> tuple[int, str]:
        self.log.info(f"Launching ParaView with {options!r}")

        # Create a tempfile and write the SLURM Config and log files into it
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        job_dir = Path(mkdtemp(prefix=os.getenv("USER"), dir=self.temp_dir))
        job_path = (job_dir / "paraview.job").resolve()

        template = Template(self.job_script_template.read_text())
        template_options = options.model_dump()
        template_options["stdout"] = (job_dir / "stdout").resolve()
        template_options["stderr"] = (job_dir / "stderr").resolve()

        with open(job_path, "w") as job_file:
            job_file.write(template.render(template_options))

        self.log.info(f"Job files can be found in {str(job_dir)!r}")
        return await output("sbatch", str(job_path), logger=self.log)
