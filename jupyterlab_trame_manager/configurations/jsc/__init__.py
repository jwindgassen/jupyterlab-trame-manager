import asyncio
import os
from pathlib import Path
from re import findall

from jupyterlab_trame_manager.configuration import Configuration, UserData, ParaViewInstance, ParaViewLaunchOptions
from jupyterlab_trame_manager.mixins.slurm import SlurmMixin
from jupyterlab_trame_manager.cmd import output


SUPPORTED_PARTITIONS = {
    "juwelsbooster": ["booster", "develbooster"],
    "juwels": ["batch", "mem192", "devel", "gpus", "develgpus"],
    "jureca": ["dc-cpu", "dc-cpu-bigmem", "dc-cpu-devel", "dc-gpu", "dc-gpu-devel"],
    "jusuf": ["batch", "scraper", "gpus", "develgpus"],
}

async def _get_account_partition_associations() -> list[tuple[str, str]]:
    # Query all valid associations between Account and Partition from Slurm.
    # To prevent submitting across cluster (e.g., JUWELS Booster <-> JUWELS Cluster),
    # we filter with a predefined selection of paritions.
    partitions = ",".join(SUPPORTED_PARTITIONS[os.environ["SYSTEMNAME"]])
    _, out = await output(
        "sacctmgr",
        "show", "association", f"{partitions=}", "format=Account,Partition",
        "--parsable2", "--noheader"
    )
    lines = out.splitlines()
    return [tuple(line.split("|")) for line in lines]


class JscConfiguration(Configuration, SlurmMixin):
    job_script_template = Path(__file__).parent / "paraview-template.jinja2"
    temp_dir = Path(os.getenv("SCRATCH"), "trame-manager-jobs")

    def get_connection_address(self, server: ParaViewInstance) -> str:
        cluster = os.environ["SYSTEMNAME"]

        if cluster == "juwelsbooster":
            root_node = findall(r"jwb\[?(\d{4})", server.node_list)[0]
            server.root_node = root_node
            return f"jwb{root_node}i.juwels"

        if cluster == "juwels":
            root_node = findall(r"jwc(\d{2}n\[?\d{2,})", server.node_list)[0].replace("[", "")
            server.root_node = root_node
            return f"jwc{root_node}i.juwels"

        if cluster == "jurecadc":
            root_node = findall(r"jrc\[?(\d{4})", server.node_list)[0]
            server.root_node = root_node
            return f"jrc{root_node}i.jureca"

        if cluster == "jusuf":
            root_node = findall(r"jsfc\[?(\d{3,})", server.node_list)[0]
            server.root_node = root_node
            return f"jsfc{root_node}i.jusuf"

        raise ValueError(f"Unknown {cluster = !r}")

    async def launch_paraview(self, options: ParaViewLaunchOptions) -> tuple[int, str]:
        options.cluster = os.environ["SYSTEMNAME"]  # Needed for Template
        return await super().launch_paraview(options)

    async def get_user_data(self) -> UserData:
        username, associations = await asyncio.gather(
            output("whoami"),
            _get_account_partition_associations()
        )

        accounts = {assoc[0] for assoc in associations}
        partitions = {assoc[1] for assoc in associations}

        return UserData(user=username[1], accounts=list(accounts), partitions=list(partitions))
