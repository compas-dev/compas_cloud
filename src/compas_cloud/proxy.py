import socket
import json

from compas.utilities import DataEncoder
from compas.utilities import DataDecoder

import compas

import time
import inspect

from .remote import Remote


class Proxy():

    def __init__(self):

        self.remote = Remote()
        self.socket = self.remote._server
        self.callbacks = {}
        print('connected to server!')

    def package(self, package, cache=False):
        return lambda *args, **kwargs: self.run(package, cache, *args, **kwargs)

    def recvall(self):
        BUFF_SIZE = 4096  # 4 KiB
        data = b''
        while True:
            part = self.socket.recv(BUFF_SIZE)
            data += part
            if len(part) < BUFF_SIZE:
                # either 0 or end of data
                break
        return data

    def send(self, data):
        """encode given data and send to remote and parse returned result"""
        istring = json.dumps(data, cls=DataEncoder)
        self.socket.send(istring.encode())
        result = self.recvall().decode()
        result = json.loads(result, cls=DataDecoder)

        # keep receiving if it is a callback
        while True:
            if isinstance(result, dict):
                if 'callback' in result:
                    # print(result['callback']['id'])
                    cb = result['callback']
                    self.callbacks[cb['id']](*cb['args'], **cb['kwargs'])
                    result = self.recvall().decode()
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

if __name__ == "__main__":
    pass
