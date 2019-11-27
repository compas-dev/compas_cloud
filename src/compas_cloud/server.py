from autobahn.twisted.websocket import WebSocketServerProtocol

from compas.utilities import DataEncoder
from compas.utilities import DataDecoder
import importlib
import json



class MyServerProtocol(WebSocketServerProtocol):

    cached = {}

    def onConnect(self, request):
        print("Client connecting: {}".format(request.peer))

    def onClose(self, wasClean, code, reason):
        print("WebSocket connection closed: {}".format(reason))

    def onMessage(self, payload, isBinary):
        result = self.process(payload)
        self.sendMessage(result.encode(), isBinary)

    def callback(self, _id, *args, **kwargs):
        data = {'callback': {'id': _id, 'args': args, 'kwargs': kwargs}}
        istring = json.dumps(data, cls=DataEncoder)
        self.sendMessage(istring.encode())

    def load_cached(self, data):
        # load cached data
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
                    self.cached[_id] = lambda *args, **kwargs: self.callback(_id, *args, **kwargs)
                    data['kwargs'][key] = self.cached[_id]


    def execute(self, data):
        package = data['package']
        names = package.split('.')
        name = '.'.join(names[:2])
        module = importlib.import_module(name)
        function = getattr(module, names[2])

        self.load_cached(data)

        if data['cache']:
            to_cache = function(*data['args'], **data['kwargs'])
            self.cached[id(to_cache)] = to_cache
            result = {'cached': id(to_cache)}
        else:
            result = function(*data['args'], **data['kwargs'])
        return result

    def get(self, data):
        _id = data['get']
        return self.cached[_id]

    def cache(self, data):
        to_cache = data['cache']
        _id = id(to_cache)
        self.cached[_id] = to_cache
        return {'cached': _id}

    def cache_func(self, data):

        print(data['cache_func'])

        name = data['cache_func']['name']
        exec(data['cache_func']['source'])
        exec('self.cached[name] = {}'.format(name))
        print(self.cached[name])
        return {'cached_func': name}


    def process(self, data):
        data = json.loads(data, cls=DataDecoder)

        if 'cache' in data:
            result = self.cache(data)

        if 'cache_func' in data:
            result = self.cache_func(data)

        if 'package' in data:
            result = self.execute(data)

        if 'get' in data:
            result = self.get(data)

        istring = json.dumps(result, cls=DataEncoder)
        return istring

if __name__ == '__main__':

    import sys

    from twisted.python import log
    from twisted.internet import reactor
    log.startLogging(sys.stdout)

    from autobahn.twisted.websocket import WebSocketServerFactory
    factory = WebSocketServerFactory()
    factory.protocol = MyServerProtocol

    reactor.listenTCP(9000, factory)
    reactor.run()
