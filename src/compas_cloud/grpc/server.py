# app.py
from concurrent import futures
import grpc

from generated import fd_pb2_grpc
from fd import Fd


class Server:

    @staticmethod
    def run():
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        fd_pb2_grpc.add_FdServicer_to_server(Fd(), server)
        server.add_insecure_port('[::]:50051')
        server.start()
        print('started')
        server.wait_for_termination()

# __main__.py
from server import Server

if __name__ == '__main__':
    Server.run()