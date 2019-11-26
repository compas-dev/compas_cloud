
from __future__ import print_function

import logging
import math

from System import Array
from System import ArraySegment
from System import Byte
from System import Uri
from System import UriBuilder
from System.Net.WebSockets import ClientWebSocket
from System.Net.WebSockets import WebSocketCloseStatus
from System.Net.WebSockets import WebSocketMessageType
from System.Net.WebSockets import WebSocketReceiveResult
from System.Net.WebSockets import WebSocketState
from System.Text import Encoding
from System.Threading import CancellationTokenSource
from System.Threading import SemaphoreSlim


import time

SEND_CHUNK_SIZE = 1024
RECEIVE_CHUNK_SIZE = 1024

__all__ = ['Client']


class Client():

    def __init__(self, host='127.0.0.1', port=9000, is_secure=False):

        if port is None:
            uri = Uri(host)
        else:
            scheme = 'wss' if is_secure else 'ws'
            builder = UriBuilder(scheme, host, port)
            uri = builder.Uri

        self.token = CancellationTokenSource().Token
        self.socket = ClientWebSocket()
        task = self.socket.ConnectAsync(uri, self.token)
        task.Wait()
        print('ready')

    def disconnect(self):
        task = self.socket.CloseAsync(WebSocketCloseStatus.NormalClosure, 'script finished', self.token)
        task.Wait()
        print('closed!')

    def send(self, payload):

        if self.socket.State != WebSocketState.Open:
            raise RuntimeError('Connection is not open.')

        message_buffer = Encoding.UTF8.GetBytes(payload)
        message_length = len(message_buffer)
        chunks_count = int(math.ceil(float(message_length) / SEND_CHUNK_SIZE))
        i = 0

        while True:
            # print('sending chunk', i)
            offset = SEND_CHUNK_SIZE * i
            is_last_message = (i == chunks_count - 1)

            if is_last_message:
                count = message_length - offset
            else:
                count = SEND_CHUNK_SIZE
            message_chunk = ArraySegment[Byte](message_buffer, offset, count)
            task = self.socket.SendAsync(message_chunk, WebSocketMessageType.Text, is_last_message, self.token)
            task.Wait()
            i += 1

            if is_last_message:
                return True

    def receive(self):

        if self.socket.State != WebSocketState.Open:
            raise RuntimeError('Connection is not open.')

        chunks = []
        while True:
            # print('receive chunk')
            buffer = Array.CreateInstance(Byte, RECEIVE_CHUNK_SIZE)
            task = self.socket.ReceiveAsync(ArraySegment[Byte](buffer), self.token)
            task.Wait()
            chunk = Encoding.UTF8.GetString(buffer)
            chunks.append(chunk)
            if task.Result.EndOfMessage:
                return ''.join(chunks).rstrip('\x00')

# import json

# client = Client()

# j = {'yes': 'yeah'}

# client.send(json.dumps(j))
# m = client.receive()
# print(json.loads(m)['yes'])

# client.disconnect()
