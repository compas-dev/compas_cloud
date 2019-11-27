import asyncio
import websockets


import json

__all__ = ['Client_Websokets']


class Client_Websokets():

    def __init__(self):
        async def connect():
            uri = "ws://127.0.0.1:9000"
            self.websocket = await websockets.connect(uri)
        asyncio.get_event_loop().run_until_complete(connect())
        print('connected to cloud using websockets client!')

    def send(self, payload):
        async def _send():
            await self.websocket.send(payload)
            return True
        return asyncio.get_event_loop().run_until_complete(_send())

    def receive(self):
        async def _receive():
            return await self.websocket.recv()
        return asyncio.get_event_loop().run_until_complete(_receive())
