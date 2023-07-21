import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from jinja2 import Template
from jupyter_server.base.handlers import APIHandler
from tornado.web import authenticated
from .cmd import run, output


async def _get_running_servers():
    out = await output("squeue", "--me", "--noheader", "--Format='Partition,Account,NumNodes,TimeUsed,TimeLimit,State,NodeList'")
    
    servers = []
    for server in out.splitlines():
        print(server)
        partition, account, nodes, timeUsed, timeLimit, state, *nodelist = server.split()
        servers.append({
            "partition": partition,
            "account": account,
            "nodes": int(nodes),
            "timeUsed": timeUsed,
            "timeLimit": timeLimit,
            "state": state,
            "url": f"jwb{nodelist[4:8]}i.juwels:11111" if state == "RUNNING" else None
        })
        
    return servers


async def _launch_paraview(options):
    print("Launching: ", options)
    input_file = Path(__file__).parent / ".." / "share" / "launch_paraview.in"
    template = Template(input_file.read_text())
    
    # Create a tempfile and write the SLURM Config into it
    with NamedTemporaryFile("w", delete=False) as tmp:
        path = tmp.name
        tmp.write(template.render(options))
    
    print(f"{path = }")
    await run("sbatch", path)


class ParaViewHandler(APIHandler):
    @authenticated
    async def get(self):
        servers = await _get_running_servers()
        await self.finish(json.dumps(servers))
        
    @authenticated
    async def post(self):
        try:
            await _launch_paraview(json.loads(self.request.body))
            self.set_status(200)
            await self.finish()
            
        except Exception as e:
            print(e)
            self.set_status(400)
            await self.finish(str(e))
