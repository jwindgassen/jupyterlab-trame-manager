import json
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
from tornado.web import authenticated


class UserRouteHandler(APIHandler):
    @authenticated
    def get(self):
        self.finish({
            "user": "windgassen1",
            "accounts": ["ccstvs", "dems", "turbulencesl"],
            "partitions": ["juwels", "booster", "devel", "develbooster"]
        })


class ParaViewHandler(APIHandler):
    @authenticated
    def get(self):
        self.finish(json.dumps([
            {
                "account": "dems",
                "partition": "booster",
                "nodes": 16,
                "runtime": "04:00:00",
                "state": "Running",
                "url": "jwb0183i:22222"
            },
            {
                "account": "ccstvs",
                "partition": "devel",
                "nodes": 1,
                "runtime": "00:30:00",
                "state": "Completing",
                "url": "jwb0001i:22222"
            }
        ]))


class TrameHandler(APIHandler):
    @authenticated
    def get(self):
        self.finish(json.dumps([
            {
                "name": "juviz",
                "path": "/p/software/stages/2023/juwelsbooster/trame/0.1.0/share/app/",
                "instances": [
                    "jwb0068.fz-juelich.de:6842",
                    "jwb0270.fz-juelich.de:9716"
                ]
            },
            {
                "name": "my-trame-app",
                "path": "/p/project/dems/windgassen1/my-trame-app/",
                "instances": [
                    "jwb0031.fz-juelich.de:8081"
                ]
            }
        ]))


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = url_path_join(web_app.settings["base_url"], "jupyter-viz-extension")
    web_app.add_handlers(host_pattern, [
        (url_path_join(base_url, "paraview"), ParaViewHandler),
        (url_path_join(base_url, "trame"), TrameHandler),
        (url_path_join(base_url, "user"), UserRouteHandler)
    ])
