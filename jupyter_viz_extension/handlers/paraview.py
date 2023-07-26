import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from jinja2 import Template
from jupyter_server.base.handlers import APIHandler
from tornado.web import authenticated
from .cmd import run, output


class ParaViewHandler(APIHandler):
    async def get_running_servers(self):
        out = await output("squeue", "--me", "--noheader", "--Format='Partition,Account,NumNodes,TimeUsed,TimeLimit,State,NodeList'")

        servers = []
        for server in out.splitlines():
            self.log.info(f"Found Server: {server}")
            partition, account, nodes, time_used, time_limit, state, *nodelist = server.split()
            servers.append({
                "partition": partition,
                "account": account,
                "nodes": int(nodes),
                "timeUsed": time_used,
                "timeLimit": time_limit,
                "state": state,
                "url": f"jwb{nodelist[4:8]}i.juwels:11111" if state == "RUNNING" else None
            })

        return servers

    async def launch_paraview(self, options):
        self.log.info(f"Launching ParaView with Options {options!r}")

        input_file = Path(__file__).parent / ".." / "share" / "launch_paraview.in"
        template = Template(input_file.read_text())

        # Create a tempfile and write the SLURM Config into it
        with NamedTemporaryFile("w", delete=False) as tmp:
            path = tmp.name
            tmp.write(template.render(options))

        self.log.info(f"Job script in {path!r}")
        await run("sbatch", path, logger=self.log)

    @authenticated
    async def get(self):
        servers = await self.get_running_servers()
        await self.finish(json.dumps(servers))
        
    @authenticated
    async def post(self):
        try:
            await self.launch_paraview(json.loads(self.request.body))
            self.set_status(200)
            await self.finish()
            
        except Exception as e:
            self.log.error(str(e))
            self.set_status(400)
            await self.finish(str(e))
