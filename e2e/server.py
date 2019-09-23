#!/usr/bin/env python3

import os
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler


class RequestHandler(BaseHTTPRequestHandler):

    def __init__(self, app_name, app_port, *args, **kwargs):
        self.app_name = app_name
        self.app_port = app_port
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"Hello, it's {self.app_name} listening on port {self.app_port}".encode())


if __name__ == "__main__":
    app_name = os.getenv("APP_NAME") or 'App1'
    app_port = os.getenv("APP_PORT") or 80
    handler = partial(RequestHandler, app_name, app_port)
    httpd = HTTPServer(('', int(app_port)), handler)
    print(f'{app_name} listening on port {app_port}')
    httpd.serve_forever()
