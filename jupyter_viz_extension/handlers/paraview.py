import json
from jupyter_server.base.handlers import APIHandler
from tornado.web import authenticated

from ..model import Model


class ParaViewHandler(APIHandler):
    _model: Model

    def initialize(self, model):
        self._model = model

    @authenticated
    async def get(self):
        await self.finish(json.dumps(
            [server.dump() for server in self._model.servers]
        ))
        
    @authenticated
    async def post(self):
        try:
            return_code, message = await self._model.launch_paraview(json.loads(self.request.body))
            self.set_status(200)
            await self.finish({"returnCode": return_code, "message": message})
            
        except Exception as e:
            self.log.error(str(e))
            self.set_status(400)
            await self.finish(str(e))
