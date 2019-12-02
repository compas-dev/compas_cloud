
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

__all__ = ['Client_Net']


class Client_Net():
    """A Websoket client using .NET that works in a simple synchronous fashion

    Parameters
    ----------

    host: str, optional
        The host ip of remote server.
        Default is ``127.0.0.1``.

    port : int, optional
        The port number of remote server to connect to.
        Default is ``9000``.

    """
    def __init__(self, host='127.0.0.1', port=9000):
        """init the client, wait until it successfully connected to server"""
        scheme = 'ws'
        builder = UriBuilder(scheme, host, port)
        uri = builder.Uri

        self.token = CancellationTokenSource().Token
        self.socket = ClientWebSocket()
        task = self.socket.ConnectAsync(uri, self.token)
        task.Wait()
        print('connected to cloud using .NET client!')

    def disconnect(self):
        """disconnect from server"""
        task = self.socket.CloseAsync(
            WebSocketCloseStatus.NormalClosure, 'script finished', self.token)
        task.Wait()
        print('closed!')

    def send(self, payload):
        """send a message to server and wait until sent"""
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
            task = self.socket.SendAsync(
                message_chunk, WebSocketMessageType.Text, is_last_message, self.token)
            task.Wait()
            i += 1

            if is_last_message:
                return True

    def receive(self):
        """listen to a message until received one"""
        if self.socket.State != WebSocketState.Open:
            raise RuntimeError('Connection is not open.')

        chunks = []
        while True:
            # print('receive chunk')
            buffer = Array.CreateInstance(Byte, RECEIVE_CHUNK_SIZE)
            task = self.socket.ReceiveAsync(
                ArraySegment[Byte](buffer), self.token)
            task.Wait()
            chunk = Encoding.UTF8.GetString(buffer)
            chunks.append(chunk)
            if task.Result.EndOfMessage:
                return ''.join(chunks).rstrip('\x00')
