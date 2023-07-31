import json
import os
from jupyter_server.base.handlers import APIHandler
from tornado.web import authenticated

from ..model import Model


class TrameHandler(APIHandler):
    _model: Model

    def initialize(self, model):
        self._model = model

    @authenticated
    async def get(self):
        await self.finish(json.dumps([
            app.dump() for app in self._model.apps.values()
        ]))
    
    @authenticated
    async def post(self):
        try:
            app_name = self.get_json_body()["appName"]
            name = self.get_json_body()["name"]
            data_directory = self.get_json_body()["dataDirectory"]
            self.log.info(f"Launching new trame instance {app_name!r}")

            if not os.path.exists(data_directory):
                self.log.error(f"Data Directory {data_directory!r} does not exist, defaulting to User's Home directory")
                data_directory = os.path.expanduser("~")

            instance = await self._model.launch_trame(app_name, name, data_directory)
            self.set_status(200)
            await self.finish(instance.dump())
            
        except Exception as e:
            self.log.error(str(e))
            self.set_status(400)
            await self.finish(str(e))
