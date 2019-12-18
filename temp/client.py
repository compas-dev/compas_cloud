import asyncio
import websockets

async def hello():
    uri = "ws://localhost:9000"
    async with websockets.connect(uri) as websocket:
    
        await websocket.send("from client")

        while True:
            response = await websocket.recv()
            print(response)

asyncio.get_event_loop().run_until_complete(hello())