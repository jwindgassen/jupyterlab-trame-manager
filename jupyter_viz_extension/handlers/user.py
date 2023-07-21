import json
import asyncio
from jupyter_server.base.handlers import APIHandler
from tornado.web import authenticated
from .cmd import output


async def _get_accounts():
    out = await output("jutil", "user", "projects", "--format='json'")
    return [group["unixgroup"] for group in json.loads(out)] if out else []
    

async def _get_partitions():
    return ["booster", "develbooster"]
    
    
class UserHandler(APIHandler):
    @authenticated
    async def get(self):
        username, accounts, partitions = await asyncio.gather(
            output("whoami"),
            _get_accounts(),
            _get_partitions()
        )
        
        await self.finish({
            "user": username,
            "accounts": accounts,
            "partitions": partitions
        })
        