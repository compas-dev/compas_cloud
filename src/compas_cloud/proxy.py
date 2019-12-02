import json

from compas.utilities import DataEncoder
from compas.utilities import DataDecoder

import compas

import time
import inspect

from subprocess import Popen
from subprocess import PIPE

if compas.is_ironpython():
    from .client_net import Client_Net as Client
else:
    from .client_websockets import Client_Websokets as Client

__all__ = ['Proxy']

class Proxy():
    """Proxy is the interface between the user and a websocket client which communicates to websoket server in background.

    Parameters
    ----------
    port : int, optional
        The port number on the remote server.
        Default is ``9000``.

    Notes
    -----

    The service will make the correct (version of the requested) functionality available
    even if that functionality is part of a virtual environment. This is because it
    will use the specific python interpreter for which the functionality is installed to
    start the server.

    If possible, the proxy will try to reconnect to an already existing service

    The proxy will implement corresponding client with either python websokets library or
    .NET depending on environment.

    Examples
    --------

    .. code-block:: python

        from compas_cloud import Proxy
        p = Proxy()
        dr_numpy = p.package('compas.numerical.dr_numpy')


    """

    def __init__(self, host='127.0.0.1', port=9000):
        """init function that starts a remote server then assigns corresponding client(websockets/.net) to the proxy"""
        self._python = compas._os.select_python(None)
        self.host = host
        self.port = port
        self.client = self.try_reconnect()
        if not self.client:
            self.client = self.start_server()
        self.callbacks = {}

    def package(self, package, cache=False):
        """returns wrapper of function that will be executed on server side"""
        return lambda *args, **kwargs: self.run(package, cache, *args, **kwargs)

    def send(self, data):
        """encode given data before sending to remote server then parse returned result"""
        istring = json.dumps(data, cls=DataEncoder)
        success = self.client.send(istring)

        result = self.client.receive()
        result = json.loads(result, cls=DataDecoder)

        # keep receiving response until a non-callback result is returned
        while True:
            if isinstance(result, dict):
                if 'callback' in result:
                    cb = result['callback']
                    self.callbacks[cb['id']](*cb['args'], **cb['kwargs'])
                    result = self.client.receive()
                    result = json.loads(result, cls=DataDecoder)
                else:
                    break
            else:
                break

        return result

    def run(self, package, cache, *args, **kwargs):
        """pass the arguments to remote function and wait to receive the results"""
        args, kwargs = self.parse_callbacks(args, kwargs)
        idict = {'package': package, 'cache': cache,
                 'args': args, 'kwargs': kwargs}
        result = self.send(idict)
        if 'error' in result:
            raise Exception(result['error'])
        return result

    def get(self, cached_object):
        """get content of a cached object stored remotely"""
        idict = {'get': cached_object['cached']}
        return self.send(idict)

    def cache(self, data):
        """cache data or function to remote server and return a reference of it"""
        if callable(data):
            idict = {'cache_func': {
                'name': data.__name__,
                'source': inspect.getsource(data)
            }}
        else:
            idict = {'cache': data}
        return self.send(idict)

    def parse_callbacks(self, args, kwargs):
        """replace a callback functions with its cached reference then sending it to server"""
        for i, a in enumerate(args):
            cb = a
            if callable(cb):
                args[i] = {'callback': {'id': id(cb)}}
                self.callbacks[id(cb)] = cb
        for key in kwargs:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = {'callback': {'id': id(cb)}}
                self.callbacks[id(cb)] = cb
        return args, kwargs

    def try_reconnect(self):
        """try to reconnect to a existing server"""
        try:
            client = Client(self.host, self.port)
        except Exception:
            return None
        else:
            print("Reconnected to an existing server at {}:{}".format(self.host, self.port))
        return client

    def start_server(self):
        """use Popen to start a remote server in background"""
        env = compas._os.prepare_environment()

        args = [self._python, '-m', 'compas_cloud.server', str(self.port)]
        self._process = Popen(args, stdout=PIPE, stderr=PIPE, env=env)
        # import sys
        # self._process = Popen(args, stdout=sys.stdout, stderr=sys.stderr, env=env)

        print("Starting new cloud server in background at {}:{}".format(self.host, self.port))

        success = False
        count = 20
        while count:
            try:
                time.sleep(0.2)
                client = Client(self.host, self.port)
            except Exception:
                count -= 1
                print("    {} attempts left.".format(count))
            else:
                success = True
                break
        if not success:
            raise RuntimeError("The server is not available.")
        else:
            print("server started with port", self.port)

        return client

if __name__ == "__main__":
    pass
