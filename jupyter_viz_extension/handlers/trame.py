import json
from jupyter_server.base.handlers import APIHandler
from tornado.web import authenticated

from ..trame_model import TrameModel


class TrameHandler(APIHandler):
    @authenticated
    async def get(self):
        await self.finish(json.dumps([
            app.dump() for app in TrameModel.instance(self.log).apps.values()
        ]))
    
    @authenticated
    async def post(self):
        app_name = self.get_argument("app_name", "juviz")
        self.log.info(f"Launching new trame instance {app_name!r}")

        try:
            instance = await TrameModel.instance(self.log).launch_trame(app_name)
            self.set_status(200)
            await self.finish(instance.dump())
            
        except Exception as e:
            self.log.error(str(e))
            self.set_status(400)
            await self.finish(str(e))
