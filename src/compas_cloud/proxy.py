import socket
import json

from compas.utilities import DataEncoder
from compas.utilities import DataDecoder

import compas

import time


class Proxy():

    def __init__(self):
        # connect to websocket server
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect(('127.0.0.1', 5005))
        

    def package(self, package):
        return lambda *args, **kwargs: self.run(package, *args, **kwargs)

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


    def run(self, package, *args, **kwargs):


        # encode args and send to rpc
        idict = {'package': package, 'args': args, 'kwargs': kwargs}
        istring = json.dumps(idict, cls=DataEncoder)

        # print('sending: ', istring)
        print('sending')

        self.socket.send(istring.encode())
        result = self.recvall()
        # decode returned result from rpc
        return json.loads(result.decode(), cls=DataDecoder)


if __name__ == "__main__":

    from compas.geometry import Translation

    T = Translation([100, 0, 0]).matrix

    p = Proxy()
    transform_points_numpy = p.package('compas.geometry.transform_points_numpy')

    r = transform_points_numpy([[0, 0, 0]], T)

    print(r)
