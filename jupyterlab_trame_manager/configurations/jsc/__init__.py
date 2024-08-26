import asyncio
import os
from json import loads
from pathlib import Path

from jupyterlab_trame_manager.configuration import Configuration, UserData
from jupyterlab_trame_manager.mixins.slurm import SlurmMixin
from jupyterlab_trame_manager.cmd import output


async def _get_accounts():
    _, out = await output("jutil", "user", "projects", "--format='json'")
    return [group["unixgroup"] for group in loads(out)] if out else []


async def _get_partitions():
    return ["booster", "develbooster"]


class JscConfiguration(Configuration, SlurmMixin):
    job_script_template = Path(__file__).parent / "paraview_juwelsbooster.in"
    temp_dir = Path(os.getenv("SCRATCH"), "trame-manager-jobs")
    node_name_regex = r"jwb\[?(\d{4})"
    server_address = "jwb%(root_node)si.juwels"

    async def get_user_data(self) -> UserData:
        username, accounts, partitions = await asyncio.gather(
            output("whoami"),
            _get_accounts(),
            _get_partitions()
        )

        return UserData(user=username[1], accounts=accounts, partitions=partitions)
