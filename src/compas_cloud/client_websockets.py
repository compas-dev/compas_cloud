import asyncio
import websockets

__all__ = ['Client_Websokets']


class Client_Websokets():
    """A Websoket client using webseckts and asyncio that works in a simple synchronous fashion

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
        async def connect():
            uri = "ws://{}:{}".format(host, str(port))
            self.websocket = await websockets.connect(uri)
        asyncio.get_event_loop().run_until_complete(connect())
        print('connected to cloud using websockets client!')

    def send(self, payload):
        """send a message to server and wait until sent"""
        async def _send():
            await self.websocket.send(payload)
            return True
        return asyncio.get_event_loop().run_until_complete(_send())

    def receive(self):
        """listen to a message until received one"""
        async def _receive():
            return await self.websocket.recv()
        return asyncio.get_event_loop().run_until_complete(_receive())
