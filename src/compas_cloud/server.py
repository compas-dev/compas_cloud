import socket
import threading

from compas.utilities import DataEncoder
from compas.utilities import DataDecoder
import importlib
import json


class Session():
    """a stateful client session which could store data across multiple calls"""

    def __init__(self, connection):
        print('a client connected!', connection)
        self.connection = connection
        self.cached = {}
        self.run()

    def recvall(self):
        BUFF_SIZE = 4096  # 4 KiB
        data = b''
        while True:
            part = self.connection.recv(BUFF_SIZE)
            data += part
            if len(part) < BUFF_SIZE:
                # either 0 or end of data
                break
        return data

    def run(self):
        # keep the connection up until client leaves
        while True:
            data = self.recvall()
            if not data:
                print('client disconnected')
                break

            result = self.process(data)

            # send back results
            conn.sendall(result)

    def load_cached(self, data):
        # load cached data
        for i, a in enumerate(data['args']):
            if 'cached' in a:
                data['args'][i] = self.cached[a['cached']]
        for key in data['kwargs']:
            if 'cached' in data['kwargs'][key]:
                data['kwargs'][key] = self.cached[data['kwargs'][key]['cached']]

    def execute(self, data):
        package = data['package']
        names = package.split('.')
        name = '.'.join(names[:2])
        module = importlib.import_module(name)
        function = getattr(module, names[2])

        self.load_cached(data)

        if data['cache']:
            to_cache = function(*data['args'], **data['kwargs'])
            self.cached[id(to_cache)] = to_cache
            result = {'cached': id(to_cache)}
        else:
            result = function(*data['args'], **data['kwargs'])
        return result

    def get(self, data):
        _id = data['get']
        return self.cached[_id]

    def cache(self, data):
        to_cache = data['cache']
        _id = id(to_cache)
        self.cached[_id] = to_cache
        return {'cached': _id}

    def process(self, data):
        data = json.loads(data, cls=DataDecoder)

        if 'cache' in data:
            result = self.cache(data)

        if 'package' in data:
            result = self.execute(data)

        if 'get' in data:
            result = self.get(data)

        istring = json.dumps(result, cls=DataEncoder)
        return istring.encode()




if __name__ == "__main__":

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 5005))
    s.listen()
    print('started listen to clients...')
    # keep listening to new clients
    while True:
        conn, addr = s.accept()
        # start a new thread for each client
        threading.Thread()
        t = threading.Thread(target=lambda conn: Session(conn), args=(conn,))
        t.start()
