from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import time
import json

import compas
import socket

from subprocess import Popen
from subprocess import PIPE


import compas._os
from compas.rpc import RPCServerError

__all__ = ['Remote']


class Remote(object):
    """a remote controller than open and close a subprocess that runs a server"""


    def __init__(self, package=None, python=None, url='http://127.0.0.1', port=5005, service='compas_cloud.server'):
        self._package = None
        self._python = compas._os.select_python(python)
        self._url = url
        self._port = port
        self._service = None
        self._process = None
        self._function = None
        self._profile = None

        self.service = service
        self.package = package

        self._implicitely_started_server = False
        self._server = self.try_reconnect()
        if self._server is None:
            self._server = self.start_server()
            self._implicitely_started_server = True

    def __enter__(self):
        return self

    def __exit__(self, *args):
        # If we started the RPC server, we will try to clean up and stop it
        # otherwise we just disconnect from it
        print('shut down server')
        if self._implicitely_started_server:
            self.stop_server()
        else:
            self._server.__close()
        pass

    @property
    def address(self):
        return "{}:{}".format(self._url, self._port)


    def try_reconnect(self):
        """Try and reconnect to an existing proxy server.

        Returns
        -------
        ServerProxy
            Instance of the proxy if reconnection succeeded,
            otherwise ``None``.
        """
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect(('127.0.0.1', 5005))
        except Exception:
            return None
        else:
            print("Reconnecting to an existing server proxy.")
        return server

    def start_server(self):
        """Start the remote server.

        Returns
        -------
        ServerProxy
            Instance of the proxy, if the connection was successful.

        Raises
        ------
        RPCServerError
            If the server providing the requested service cannot be reached after
            100 contact attempts (*pings*).

        """
        env = compas._os.prepare_environment()

        args = [self._python, '-m', self.service, str(self._port)]
        self._process = Popen(args, stdout=PIPE, stderr=PIPE, env=env)

        # import sys
        # self._process = Popen(args, stdout=sys.stdout, stderr=sys.stderr, env=env)


        print("Starting a new proxy server...")

        success = False
        count = 100
        while count:
            try:
                time.sleep(0.1)
                server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server.connect(('127.0.0.1', 5005))
            except Exception:
                count -= 1
                print("    {} attempts left.".format(count))
            else:
                success = True
                break
        if not success:
            raise RPCServerError("The server is not available.")
        else:
            print("New proxy server started.")

        return server

    def stop_server(self):
        """Stop the remote server and terminate/kill the python process that was used to start it.
        """
        print("Stopping the server proxy.")
        try:
            self._server.remote_shutdown()
        except Exception:
            pass
        self._terminate_process()

    def _terminate_process(self):
        """Attempts to terminate the python process hosting the proxy server.

        The process reference might not be present, e.g. in the case
        of reusing an existing connection. In that case, this is a no-op.
        """
        if not self._process:
            return

        try:
            self._process.terminate()
        except Exception:
            pass
        try:
            self._process.kill()
        except Exception:
            pass



# ==============================================================================
# Main
# ==============================================================================

if __name__ == "__main__":

    pass
    # import doctest

    # doctest.testmod(globs=globals())
