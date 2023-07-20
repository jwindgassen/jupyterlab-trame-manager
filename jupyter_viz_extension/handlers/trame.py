import json
import importlib
import socket
from jupyter_server.base.handlers import APIHandler
from tornado.web import authenticated


def _next_open_port() -> int:
    "We let socket determine an available open port"
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]

        
def _launch_trame(app_name: str):
    # import the trame app as a module (for now)
    module = importlib.import_module(app_name)
    
    if not module.main:
        raise ValueError(f"Module {app_name} does not provide a 'main' function")
    
    port = _next_open_port()
    print(f"Opening on port {port}")
    task = module.main(port=port, open_browser=False, show_connection_info=True, exec_mode="task")
    print(task)
    
    return port


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
    
    @authenticated
    def post(self):
        app_name = self.get_argument("app_name", "pv_visualizer")
        
        print(f"Launching new trame instance '{app_name}'")
        
        try:
            port = _launch_trame(app_name)
            self.set_status(200)
            self.finish({"port": port})
            
        except Exception as e:
            print(e)
            self.set_status(400)
            self.finish(str(e))
        