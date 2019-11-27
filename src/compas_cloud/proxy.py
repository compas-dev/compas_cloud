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

    def __init__(self, port=9000):

        self._python = compas._os.select_python(None)
        self.port = port
        self.client = self.try_reconnect()
        if not self.client:
            self.client = self.start_server()
        self.callbacks = {}

    def package(self, package, cache=False):
        return lambda *args, **kwargs: self.run(package, cache, *args, **kwargs)

    def send(self, data):
        """encode given data and send to remote and parse returned result"""
        istring = json.dumps(data, cls=DataEncoder)
        success = self.client.send(istring)

        result = self.client.receive()
        result = json.loads(result, cls=DataDecoder)

        # keep receiving if it is a callback
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
        """proxy to run the package function"""
        args, kwargs = self.parse_callbacks(args, kwargs)
        idict = {'package': package, 'cache': cache,
                 'args': args, 'kwargs': kwargs}
        return self.send(idict)

    def get(self, cached_object):
        """get content of a cached object stored remotely"""
        idict = {'get': cached_object['cached']}
        return self.send(idict)

    def cache(self, data):
        """cache the give data and return a reference of it"""
        if callable(data):
            idict = {'cache_func': {
                'name': data.__name__,
                'source': inspect.getsource(data)
            }}
        else:
            idict = {'cache': data}
        return self.send(idict)

    def parse_callbacks(self, args, kwargs):
        "turn callback functions into a reference before sending to server"
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
        try:
            client = Client(port=self.port)
        except Exception:
            return None
        else:
            print("Reconnected to an existing server at port", self.port)
        return client

    def start_server(self):
        env = compas._os.prepare_environment()

        args = [self._python, '-m', 'compas_cloud.server', str(self.port)]
        self._process = Popen(args, stdout=PIPE, stderr=PIPE, env=env)
        # import sys
        # self._process = Popen(args, stdout=sys.stdout, stderr=sys.stderr, env=env)

        print("Starting new cloud server in background")

        success = False
        count = 20
        while count:
            try:
                time.sleep(0.2)
                client = Client(port=self.port)
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
