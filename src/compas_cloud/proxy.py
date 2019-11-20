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
        result = self.recvall()
        return json.loads(result.decode(), cls=DataDecoder)

    def run(self, package, cache, *args, **kwargs):
        """proxy to run the package function"""
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

if __name__ == "__main__":
    pass
