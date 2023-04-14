from autobahn.asyncio.websocket import WebSocketServerProtocol

import compas
import importlib
import json
from compas_cloud import Sessions
import time
import sys
import traceback
import pkg_resources
from .cache import Reference
from .cache import FunctionReference
from .payload import Payload

try:
    from compas.data import DataEncoder
    from compas.data import DataDecoder
except ImportError:
    from compas.utilities import DataEncoder
    from compas.utilities import DataDecoder


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

    # def load_cached(self, data):
    #     """detect and load cached data or callback functions in arguments"""
    #     for i, a in enumerate(data['args']):
    #         if isinstance(a, Reference):
    #             data['args'][i] = self.cached[a.cache_id]

    #     for key in data['kwargs']:
    #         if isinstance(data['kwargs'][key], Reference):
    #             data['kwargs'][key] = self.cached[data['kwargs'][key].cache_id]
    #         elif isinstance(data['kwargs'][key], dict):
    #             if 'callback' in data['kwargs'][key]:
    #                 _id = data['kwargs'][key]['callback']['id']
    #                 self.cached[_id] = lambda *args, **kwargs: self.callback(
    #                     _id, *args, **kwargs)
    #                 data['kwargs'][key] = self.cached[_id]


    def get(self, reference):
        """get cached data from its id"""
        return reference

    def get_attribute(self, data):
        raise NotImplementedError
    
    def set_attribute(self, data):
        raise NotImplementedError

    def set(self, data):
        raise NotImplementedError

    def cache(self, content):
        """cache received data and return its reference object"""
        data = content["data"]
        cache_id = content.get('cache_id', id(data))
        self.cached[cache_id] = data
        return Reference(cache_id)

    def sessions_alive(self):
        return isinstance(self.sessions, Sessions)

    def control(self, command):
        if command == 'shutdown':
            raise KeyboardInterrupt
        if command == 'check':
            print('check from client')
            return {'status': "I'm good"}
        if command == 'once':
            self.server_type = "ONCE"
            print('Setting Server type to ONCE, server will be closed once this client disconnect.')
            return {'status': "server type set as ONCE"}
        if command == 'version':
            return self.version()

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

    def call(self, content):
        """execute corresponding binded functions with received arguments"""
        function = content["function"]
        cache_result = content["cache_result"]
        args = content["args"]
        kwargs = content["kwargs"]

        # TODO: add verbose option
        start = time.time()
        print('running:', function)
        result = function(*args, **kwargs)

        if cache_result:
            cache_id = id(result)
            self.cached[cache_id] = result
            result = Reference(cache_id)

        t = time.time()-start
        print('finished in: {}s'.format(t))
        return result

    def function(self, content):
        """execute corresponding binded functions with received arguments"""
        if "package" in content:
            return self.function_from_package(content)
        elif "source" in content:
            return self.function_from_source(content)
        else:
            raise ValueError(f"Unrecognised function content:{content}")

    def function_from_package(self, content):
        """cache a excutable function"""
        package = content["package"]
        cache_result = content["cache_result"]
        names = package.split('.')
        name = '.'.join(names[:-1])
        module = importlib.import_module(name)
        function = getattr(module, names[-1])
        cache_id = id(function)
        self.cached[cache_id] = function
        return FunctionReference(cache_id, function_name=package, cache_result=cache_result)

    def function_from_source(self, content):
        """cache a excutable function"""
        function_name = content['name']
        cache_result = content["cache_result"]
        cache_id = None
        exec(content['source'])
        exec('cache_id = id(function_name)')
        exec('self.cached[cache_id] = {}'.format(function_name))
        return  FunctionReference(cache_id, function_name=function_name, cache_result=cache_result)

    def process(self, data):
        """process received data according to its payload content"""
        try:
            payload = json.loads(data, cls=ReferenceDeCoder)
            
            if not isinstance(payload, Payload):
                raise TypeError("Not a Payload object")

            if payload.type == 'control':
                result = self.control(payload.content)
            elif payload.type == 'function':
                result = self.function(payload.content)
            elif payload.type == 'cache':
                result = self.cache(payload.content)
            elif payload.type == 'get':
                result = self.get(payload.content)
            elif payload.type == 'call':
                result = self.call(payload.content)
            else:
                raise ValueError("Unrecognised payload: {}".format(payload))

            # if 'cache' in data:
            #     result = self.cache(data)

            # if 'cache_func' in data:
            #     result = self.cache_func(data)

            # if 'package' in data:
            #     result = self.execute(data)

            # if 'get' in data:
            #     result = self.get(data)

            # if 'sessions' in data:
            #     result = self.control_sessions(data)

            # if 'control' in data:
            #     result = self.control(data)

            # if 'version' in data:
            #     result = self.version()

        except BaseException as error:

            if isinstance(error, KeyboardInterrupt):
                raise KeyboardInterrupt

            exc_type, exc_value, exc_tb = sys.exc_info()
            error_payload = Payload('error', traceback.format_exception(exc_type, exc_value, exc_tb))
            print("".join(error_payload.content))
            return json.dumps(error_payload, cls=DataEncoder)

        result_payload = Payload('result', result)
        return json.dumps(result_payload, cls=DataEncoder)

    def version(self):

        working_set = pkg_resources.working_set
        packages = {p.project_name: p.version for p in working_set if p.project_name.lower().startswith('compas')}

        return {
            "COMPAS": compas.__version__,
            "Python": sys.version,
            "Packages": packages
        }

class ReferenceDeCoder(DataDecoder):
    def object_hook(self, o):
        o = super(ReferenceDeCoder, self).object_hook(o)
        if isinstance(o, Reference):
            return CompasServerProtocol.cached[o.cache_id]
        else:
            return o

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
