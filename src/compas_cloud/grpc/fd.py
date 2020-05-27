# grpc.py
from generated import fd_pb2, fd_pb2_grpc
from compas.numerical import fd_numpy
import numpy as np
from serialize import encode, decode

class Fd(fd_pb2_grpc.FdServicer):

    def Reply(self, request, context):

        vertices = decode(request.vertices)
        edges = decode(request.edges)
        fixed = decode(request.fixed)
        q = decode(request.q)
        loads = decode(request.loads)

        xyz, q, f, l, r = fd_numpy(vertices, edges, fixed, q, loads)
        
        return fd_pb2.FdReply(
            xyz = encode(xyz), 
            q = encode(q),
            f = encode(f),
            l = encode(l), 
            r = encode(r)
        )