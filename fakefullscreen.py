#!/usr/bin/env python3
#######################
# Issues:
# - some applications oversize when set to 100%/full screen size in pixels
#   gnome-terminal and emacs lose ~20 pixels at the bottom of the screen
#   firefox, chrome and xterm seem to be fine
#   it may be an .Xresources/scaling issue, unsure... seems like an i3 bug
#   so... only do this for firefox, since that's the only application that
#   benefits right now
# - if you kill the fakefullscreened window, you'll see the placeholder window

import os
import socket
import selectors
import tempfile
import threading
from argparse import ArgumentParser
import i3ipc

SOCKET_DIR = '{}/i3_fakefullscreen.{}{}'.format(tempfile.gettempdir(), os.geteuid(),
                                            os.getenv("DISPLAY"))
SOCKET_FILE = '{}/socket'.format(SOCKET_DIR)


class FocusWatcher:
    def __init__(self):
        self.i3 = i3ipc.Connection()
        # Make a directory with permissions that restrict access to
        # the user only.
        os.makedirs(SOCKET_DIR, mode=0o700, exist_ok=True)
        self.listening_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        if os.path.exists(SOCKET_FILE):
            os.remove(SOCKET_FILE)
        self.listening_socket.bind(SOCKET_FILE)
        self.listening_socket.listen(1)
        self.window = self.i3.get_tree().find_focused()
        self.window_width = self.window.rect.width
        self.window_height = self.window.rect.height
        self.max = False

    def togglemax(self):
        # use an empty marked window as a placeholder for getting the floating
        # window back where it started
        if not self.max:
            self.window = self.i3.get_tree().find_focused()
            self.window_width = self.window.rect.width
            self.window_height = self.window.rect.height
            if self.window.fullscreen_mode == 0 and self.window.window_class == "Firefox":
                self.i3.command('[con_id={0}] mark --add zoom;' \
                    '[con_mark="placeholder"] open; mark placeholder;' \
                    '[con_mark="zoom"] floating toggle;' \
                    '[con_mark="zoom"] border none;' \
                    '[con_mark="zoom"] resize set 100 ppt 100 ppt;' \
                    '[con_mark="zoom"] move position 0 0;' \
                    '[con_mark="zoom"] focus;'.format(self.window.id))
                print("maximise")
                self.max = not self.max
            else:
                self.i3.command('fullscreen toggle')
                print("native fullscreen toggle")
        else:
            self.i3.command('[con_mark="placeholder"] focus;' \
                '[con_mark="zoom"] floating toggle;' \
                '[con_mark="zoom"] border normal;' \
                '[con_mark="zoom"] focus;' \
                '[con_mark="placeholder"] kill;' \
                '[con_mark="zoom"] resize set {0} {1};'
                '[con_mark="zoom"] unmark;'.format( \
                self.window_width, self.window_height))
            print("unmaximise")
            self.max = not self.max

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
