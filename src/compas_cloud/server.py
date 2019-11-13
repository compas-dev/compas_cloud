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
            print("received data")

            result = self.process(data)

            # send back results
            conn.sendall(result)

    def process(self, data):
        data = json.loads(data, cls=DataDecoder)

        package = data['package']
        names = package.split('.')
        name = '.'.join(names[:2])
        module = importlib.import_module(name)
        function = getattr(module, names[2])
        print(function)
        result = function(*data['args'], **data['kwargs'])
        istring = json.dumps(result, cls=DataEncoder)

        return istring.encode()


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
