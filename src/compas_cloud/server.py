from autobahn.asyncio.websocket import WebSocketServerProtocol

import compas
from compas.utilities import DataEncoder
from compas.utilities import DataDecoder
import importlib
import json
from compas_cloud import Sessions
import time
import sys
import traceback
import pkg_resources


class CompasServerProtocol(WebSocketServerProtocol):
    """The CompasServerProtocol defines the behaviour of compas cloud server"""
    cached = {}
    sessions = None
    server_type = "NORMAL"

    def onConnect(self, request):
        """print client info on connection"""
        print("Client connecting: {}".format(request.peer))

    def onClose(self, wasClean, code, reason):
        """print reason on connection closes"""
        print("WebSocket connection closed: {}".format(reason))
        if self.server_type == "ONCE":
            raise KeyboardInterrupt

    def onMessage(self, payload, isBinary):
        """process the income messages"""
        result = self.process(payload)
        self.sendMessage(result.encode(), isBinary)

    def callback(self, _id, *args, **kwargs):
        """send the arguments of callback functions to client side"""
        data = {'callback': {'id': _id, 'args': args, 'kwargs': kwargs}}
        istring = json.dumps(data, cls=DataEncoder)
        self.sendMessage(istring.encode())

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

        start = time.time()
        print('running:', package)
        self.load_cached(data)

        if data['cache']:
            to_cache = function(*data['args'], **data['kwargs'])
            self.cached[id(to_cache)] = to_cache
            result = {'cached': id(to_cache)}
        else:
            result = function(*data['args'], **data['kwargs'])
        t = time.time()-start
        print('finished in: {}s'.format(t))
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
        return isinstance(self.sessions, Sessions)

    def control(self, data):
        command = data['control']
        if command == 'shutdown':
            raise KeyboardInterrupt
        if command == 'check':
            print('check from client')
            return {'status': "I'm good"}
        if command == 'once':
            self.server_type = "ONCE"
            print('Setting Server type to ONCE, server will be closed once this client disconnect.')
            return {'status': "server type set as ONCE"}

        raise ValueError("Unrecognised control command")

    def control_sessions(self, data):
        """control attached sessions according to message received"""
        s = data["sessions"]
        if s["command"] == 'create':
            if not self.sessions_alive():
                self.sessions = Sessions(socket=self)
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
                self.sessions.listen()
                self.sessions = None
                return "All sessions concluded"

            if s["command"] == 'shutdown':
                self.sessions.terminate()
                self.sessions = None

    def process(self, data):
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
                result = self.control_sessions(data)

            if 'control' in data:
                result = self.control(data)

            if 'version' in data:
                result = self.version()

        except BaseException as error:

            if isinstance(error, KeyboardInterrupt):
                raise KeyboardInterrupt

            exc_type, exc_value, exc_tb = sys.exc_info()
            result = {'error': traceback.format_exception(exc_type, exc_value, exc_tb)}
            print("".join(result['error']))

        istring = json.dumps(result, cls=DataEncoder)
        return istring

    def version(self):

        working_set = pkg_resources.working_set
        packages = set([p.project_name for p in working_set]) - set(['COMPAS'])
        compas_pkgs = [p for p in packages if p.lower().startswith('compas')]

        return {
            "COMPAS": compas.__version__,
            "Python": sys.version,
            "Extensions": compas_pkgs
        }


if __name__ == '__main__':

    import argparse

    try:
        import asyncio
    except ImportError:
        # Trollius >= 0.3 was renamed
        import trollius as asyncio

    from autobahn.asyncio.websocket import WebSocketServerFactory
    factory = WebSocketServerFactory()
    factory.protocol = CompasServerProtocol

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=9009)
    args = parser.parse_args()

    ip = '127.0.0.1'
    port = int(args.port)

    loop = asyncio.get_event_loop()
    coro = loop.create_server(factory, '127.0.0.1', port)
    server = loop.run_until_complete(coro)
    print("starting compas_cloud server")
    print("Listenning at %s:%s" % (ip, port))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        print("shuting down server")
        server.close()
        loop.close()
