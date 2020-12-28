#!/usr/bin/env python3

import os
import socket
import selectors
import tempfile
import threading
from argparse import ArgumentParser
import i3ipc
import subprocess

SOCKET_DIR = '{}/i3_fakefullscreen.{}{}'.format(tempfile.gettempdir(), os.geteuid(),
                                            os.getenv("DISPLAY"))
SOCKET_FILE = '{}/socket'.format(SOCKET_DIR)
MAX_WIN_HISTORY = 15


class FocusWatcher:
    def __init__(self):
        self.i3 = i3ipc.Connection()
        self.i3.on('window::focus', self.on_window_focus)
        # Make a directory with permissions that restrict access to
        # the user only.
        os.makedirs(SOCKET_DIR, mode=0o700, exist_ok=True)
        self.listening_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        if os.path.exists(SOCKET_FILE):
            os.remove(SOCKET_FILE)
        self.listening_socket.bind(SOCKET_FILE)
        self.listening_socket.listen(1)
        self.window = self.i3.get_tree().find_focused()
        self.max = False
        self.res_x = int(subprocess.check_output("xrandr | grep '*' | sed -E 's| *([0-9]*)x([0-9]*).*|\\1|g'", shell=True).decode())
        self.res_y = int(subprocess.check_output("xrandr | grep '*' | sed -E 's| *([0-9]*)x([0-9]*).*|\\2|g'", shell=True).decode())
        print("Init - detected resolution: {0}x{1}".format( self.res_x, self.res_y))

    def togglemax(self):
        # use an empty marked window as a placeholder for getting the floating
        # window back where it started
        if not self.max:
            print("maximise")
            self.i3.command('[con_id={0}] mark --add zoom;' \
                '[con_mark="placeholder"] open; mark placeholder;' \
                '[con_mark="zoom"] floating toggle;' \
                '[con_mark="zoom"] border none;' \
                '[con_mark="zoom"] move position 0 0;' \
                '[con_mark="zoom"] resize set {1} {2};' \
                '[con_mark="zoom"] focus;'.format( \
                    self.window.id, \
                    self.res_x, \
                    self.res_y))
        else:
            print("unmaximise")
            self.i3.command('[con_mark="placeholder"] focus;' \
                '[con_mark="zoom"] floating toggle;' \
                '[con_mark="zoom"] border normal;' \
                '[con_mark="zoom"] focus;' \
                '[con_mark="placeholder"] kill;' \
                '[con_mark="zoom"] unmark;')
        self.max = not self.max

    def on_window_focus(self, i3conn, event):
        # update current focused window
        self.window = event.container

    def launch_i3(self):
        self.i3.main()

    def launch_server(self):
        selector = selectors.DefaultSelector()

        def accept(sock):
            conn, addr = sock.accept()
            selector.register(conn, selectors.EVENT_READ, read)

        def read(conn):
            data = conn.recv(1024)
            if data == b'maxon':
                if not self.max:
                    self.togglemax()
            if data == b'maxoff':
                if self.max:
                    self.togglemax()
            if data == b'max':
                self.togglemax()
            elif not data:
                selector.unregister(conn)
                conn.close()

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
    parser = ArgumentParser(prog='fakefullscreen.py',
                            description='''
        i3 Fake fullscreen
        Visually it's fullscreen, but _net_wm_state is not changed
        This is beneficial for applications that do annoying things
        when they see _net_wm_state change.

        This script acts as a server when run with no args, and a client when run
        with args.

        You can bind this to keys in your i3 config or to external applications
        ''')
    parser.add_argument('--maxoff',
                        dest='maxoff',
                        action='store_true',
                        help='un-Max container',
                        default=False)
    parser.add_argument('--maxon',
                        dest='maxon',
                        action='store_true',
                        help='Max container',
                        default=False)
    parser.add_argument('--max',
                        dest='max',
                        action='store_true',
                        help='toggle Max on container',
                        default=False)
    args = parser.parse_args()

    if args.max:
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_socket.connect(SOCKET_FILE)
        client_socket.send(b'max')
        client_socket.close()
    elif args.maxon:
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_socket.connect(SOCKET_FILE)
        client_socket.send(b'maxon')
        client_socket.close()
    elif args.maxoff:
        client_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client_socket.connect(SOCKET_FILE)
        client_socket.send(b'maxoff')
        client_socket.close()
    else:
        focus_watcher = FocusWatcher()
        focus_watcher.run()
