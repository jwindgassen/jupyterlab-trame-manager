from jupyter_server.base.handlers import APIHandler
from tornado.web import authenticated

from ..model import Model


class UserHandler(APIHandler):
    _model: Model

    def initialize(self, model):
        self._model = model

    @authenticated
    async def get(self):
        user_data = await self._model.get_user_data()
        self.log.debug(f"{user_data}")

        await self.finish(user_data._asdict())
        