import asyncio
import websockets

from compas.utilities import DataEncoder
from compas.utilities import DataDecoder
import importlib
import json
from compas_cloud import Sessions
from multiprocessing import Queue


class Sessions_server(Sessions):

    socket_message = Queue()

    def log(self, *args, **kwargs):
        print(self.status, "________", *args, **kwargs)
        self.socket_message.put((self.status, "________", args))

    async def listen(self, socket):
        while not self.all_finished() or not self.messages.empty():
            self.process_message()
            await self.send_to_socket(socket)
        self.log("FINISHED")
        await self.send_to_socket(socket)

    async def send_to_socket(self, socket):
        while not self.socket_message.empty():
            msg = self.socket_message.get()
            data = json.dumps({"listen": msg})
            await socket.send(data)


class Server_Websockets():

    def __init__(self, host='127.0.0.1', port=9000):
        """init the client, wait until it successfully connected to server"""

        self.cached = {}
        self.websocket = None

        async def user_session(websocket, path):
            self.websocket = websocket
            print('user connected', websocket, path)
            self.messages_to_send = Queue()

            async def listen():
                while True:
                    try:
                        data = await self.websocket.recv()
                        result = await self.process(data)
                        await self.websocket.send(result)

                    except Exception as e:
                        print('user disconnected:', e)
                        break

            async def wait():
                i = 0
                while i < 20:

                    if self.messages_to_send.empty():
                        # print('empty')
                        pass
                    else:
                        i += 1
                        # print(self.messages_to_send.get())
                        print('callback', i)
                        # print(self.messages_to_send.get())
                        await self.websocket.send(self.messages_to_send.get())

                    await asyncio.sleep(0.01)

            await asyncio.wait([listen(), wait()])

            self.websocket = None

        start_server = websockets.serve(user_session, host, port)
        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(start_server)
        print('started server')
        self.loop.run_forever()

    def callback(self, _id, *args, **kwargs):
        """send the arguments of callback functions to client side"""
        data = {'callback': {'id': _id, 'args': args, 'kwargs': kwargs}}
        istring = json.dumps(data, cls=DataEncoder)
        self.messages_to_send.put(istring)

    def load_cached(self, data):
        """detect and load cached data or callback functions in arguments"""
        for i, a in enumerate(data['args']):
            if isinstance(a, dict):
                if 'cached' in a:
                    data['args'][i] = self.cached[a['cached']]

        for key in data['kwargs']:
            if isinstance(data['kwargs'][key], dict):
                if 'cached' in data['kwargs'][key]:
                    data['kwargs'][key] = self.cached[data['kwargs'][key]['cached']]
                if 'callback' in data['kwargs'][key]:
                    _id = data['kwargs'][key]['callback']['id']
                    self.cached[_id] = lambda *args, **kwargs: self.callback(
                        _id, *args, **kwargs)
                    data['kwargs'][key] = self.cached[_id]

    def execute(self, data):
        """execute corresponding binded functions with received arguments"""
        package = data['package']
        names = package.split('.')
        name = '.'.join(names[:-1])
        module = importlib.import_module(name)
        function = getattr(module, names[-1])

        self.load_cached(data)

        if data['cache']:
            to_cache = function(*data['args'], **data['kwargs'])
            self.cached[id(to_cache)] = to_cache
            result = {'cached': id(to_cache)}
        else:
            print('start execution of function')
            result = function(*data['args'], **data['kwargs'])

        print('execution finished')
        return result

    def get(self, data):
        """get cached data from its id"""
        _id = data['get']
        return self.cached[_id]

    def cache(self, data):
        """cache received data and return its reference object"""
        to_cache = data['cache']
        _id = id(to_cache)
        self.cached[_id] = to_cache
        return {'cached': _id}

    def cache_func(self, data):
        """cache a excutable function"""
        name = data['cache_func']['name']
        exec(data['cache_func']['source'])
        exec('self.cached[name] = {}'.format(name))
        return {'cached_func': name}

    def sessions_alive(self):
        if hasattr(self, 'sessions'):
            if isinstance(self.sessions, Sessions):
                return True
        return False

    async def control_sessions(self, data):
        s = data["sessions"]
        if s["command"] == 'create':
            if not self.sessions_alive():
                self.sessions = Sessions_server()
                return "session successfully created"
            else:
                raise RuntimeError("There is already sessions running, try to reconnect or shut down")
        else:
            if not self.sessions_alive():
                raise RuntimeError("There no running sessions, try to create one first")

            if s["command"] == 'add_task':
                func_id = s['func']['cached_func']
                func = self.cached[func_id]
                self.sessions.add_task(func, *s['args'], *s['kwargs'])
                return "task added"

            if s["command"] == 'start':
                self.sessions.start()
                return "sessions started"

            if s["command"] == 'listen':
                await self.sessions.listen(self.websocket)
                # import time
                # for i in range(10):
                #     time.sleep(1)
                #     print('sending to socket')
                #     istring = json.dumps({"listen": ("listen", i)})
                #     # print(self.sendMessage(istring.encode()))
                #     await self.websocket.send(istring)

                return "Session concluded"

            if s["command"] == 'shutdown':
                self.sessions.terminate()
                self.sessions = None

    async def process(self, data):
        """process received data according to its content"""
        data = json.loads(data, cls=DataDecoder)

        try:

            if 'cache' in data:
                result = self.cache(data)

            if 'cache_func' in data:
                result = self.cache_func(data)

            if 'package' in data:
                result = self.execute(data)

            if 'get' in data:
                result = self.get(data)

            if 'sessions' in data:
                result = await self.control_sessions(data)

        except BaseException as error:
            result = {'error': '{}:{}'.format(type(error).__name__, error)}
            print(result)

        istring = json.dumps(result, cls=DataEncoder)
        return istring


# if __name__ == "main":
Server_Websockets()
