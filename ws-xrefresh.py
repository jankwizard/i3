#!/usr/bin/env python3

import os
import socket
import selectors
import tempfile
import threading
from argparse import ArgumentParser
import i3ipc
import subprocess

SOCKET_DIR = '{}/i3_ws_xrefresh.{}{}'.format(tempfile.gettempdir(), os.geteuid(),
                                            os.getenv("DISPLAY"))
SOCKET_FILE = '{}/socket'.format(SOCKET_DIR)

class FocusWatcher:
    def __init__(self):
        self.i3 = i3ipc.Connection()
        self.i3.on('workspace::focus', self.xrefresh)
        # Make a directory with permissions that restrict access to
        # the user only.
        os.makedirs(SOCKET_DIR, mode=0o700, exist_ok=True)
        self.listening_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        if os.path.exists(SOCKET_FILE):
            os.remove(SOCKET_FILE)
        self.listening_socket.bind(SOCKET_FILE)
        self.listening_socket.listen(1)

    def xrefresh(self, i3conn, event):
        print("xrefresh")
        subprocess.call("xrefresh", shell=True)

    def launch_i3(self):
        self.i3.main()

    def launch_server(self):
        selector = selectors.DefaultSelector()

        def accept(sock):
            conn, addr = sock.accept()
            selector.register(conn, selectors.EVENT_READ, read)

        def read(conn):
            pass

        selector.register(self.listening_socket, selectors.EVENT_READ, accept)

        while True:
            for key, event in selector.select():
                callback = key.data
                callback(key.fileobj)

    def run(self):
        t_i3 = threading.Thread(target=self.launch_i3)
        t_server = threading.Thread(target=self.launch_server)
        for t in (t_i3, t_server):
            t.start()


if __name__ == '__main__':
    focus_watcher = FocusWatcher()
    focus_watcher.run()
