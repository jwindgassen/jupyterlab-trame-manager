import json
import os
import asyncio
from jupyter_server.base.handlers import APIHandler
from tornado.web import authenticated
from ..cmd import output


async def _get_accounts():
    _, out = await output("jutil", "user", "projects", "--format='json'")
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

        self.log.debug(f"User: {username!r} - Accounts: {accounts!r} - Partitions: {partitions!r}")

        await self.finish({
            "user": username,
            "home": os.path.expanduser("~"),
            "accounts": accounts,
            "partitions": partitions
        })
        