#!/usr/bin/env python3
##################
# Simple server that allows firefox to request fake "fullscreen"
# Visually it's fullscreen, but _net_wm_state is not changed
# This is intended to be used with:
#   Firefox:full-screen-api.ignore-widgets = true
# to disable normal fullscreen, and fake fullscreen enabled via a client/hook
# in firefox pages (firefox_fakefullscreen_client.js)
##################

import os
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

os.chdir(".")

class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        print(f"do_GET - {self.path}")
        self.send_response(200)
        self.end_headers()
        if self.path == "/maxoff":
            subprocess.check_output("python3 focus-last.py --maxoff", shell=True)
        elif self.path == "/maxon":
            subprocess.check_output("python3 focus-last.py --maxon", shell=True)


httpd = HTTPServer(('localhost', 8000), SimpleHTTPRequestHandler)
httpd.serve_forever()

