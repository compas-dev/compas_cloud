from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json

try:
    from compas.data import DataEncoder
    from compas.data import DataDecoder
except ImportError:
    from compas.utilities import DataEncoder
    from compas.utilities import DataDecoder

import compas

import time
import inspect

from subprocess import Popen
from functools import wraps
from .cache import Reference
from .cache import FunctionReference
from .payload import Payload

if compas.IPY:
    from .client_net import Client_Net as Client
    import Rhino
else:
    from .client_websockets import Client_Websockets as Client


__all__ = ['Proxy']


def retry_if_exception(ex, max_retries, wait=0):
    def outer(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            assert max_retries > 0
            x = max_retries
            e = RuntimeError("unknown")
            while x:
                if compas.IPY:
                    Rhino.RhinoApp.Wait()
                try:
                    return func(*args, **kwargs)
                except ex as error:
                    e = error
                    print(e)
                    if isinstance(e, ServerSideError):
                        break
                    print('proxy call failed, trying time left:', x)
                    x -= 1
                    time.sleep(wait)
            raise e
        return wrapper
    return outer


class ServerSideError(Exception):
    pass


class Proxy():
    """Proxy is the interface between the user and a websocket client which communicates to websoket server in background.

    Parameters
    ----------
    port : int, optional
        The port number on the remote server.
        Default is ``9009``.

    Notes
    -----

    The service will make the correct (version of the requested) functionality available
    even if that functionality is part of a virtual environment. This is because it
    will use the specific python interpreter for which the functionality is installed to
    start the server.

    If possible, the proxy will try to reconnect to an already existing service

    The proxy will implement corresponding client with either python websokets library or
    .NET depending on environment.

    Examples
    --------

    .. code-block:: python

        from compas_cloud import Proxy
        p = Proxy()
        dr_numpy = p.package('compas.numerical.dr_numpy')


    """

    def __init__(self, host='127.0.0.1', port=9009, background=True, errorHandler=None, once=True, start_server=True):
        """init function that starts a remote server then assigns corresponding client(websockets/.net) to the proxy"""
        self._python = compas._os.select_python(None)
        self.host = host
        self.port = port
        self.background = background
        self.client = self.try_reconnect()
        if not self.client:
            if start_server:
                self.client = self.start_server()
                if once:
                    print("Server will shut down once program finish")
                    self.once()
                else:
                    print("Server will keep running after progrom finish")
            else:
                raise ConnectionError("Failed to connect to {}:{}".format(host, port))

        self.callbacks = {}
        self.errorHandler = errorHandler

        # Hook up the reference class with this proxy.
        Reference.proxy = self

    def function(self, func, cache_result=False):
        """returns wrapper of function that will be executed on server side"""

        # TODO: add back retry.
        if callable(func):
            return self.send_and_listen(Payload("function", {'name': func.__name__,'source': inspect.getsource(func), "cache_result": cache_result}))

        elif isinstance(func, str):
            return self.send_and_listen(Payload("function", {"package": func, "cache_result": cache_result}))
        
        else:
            raise TypeError("func should be a function or a package string")

        # if self.errorHandler:
        #     @self.errorHandler
        #     @retry_if_exception(Exception, 5, wait=0.5)
        #     def run_function(*args, **kwargs):
        #         return self.run(package, cache, *args, **kwargs)

        #     return run_function
        # else:
        #     @retry_if_exception(Exception, 5, wait=0.5)
        #     def run_function(*args, **kwargs):
        #         return self.run(package, cache, *args, **kwargs)

        #     return run_function
    
    def call(self, function, *args, **kwargs):
        """call a function on a cached object"""
        return self.send_and_listen(Payload("call", {"function": function, "args": args, "kwargs": kwargs, "cache_result": function.cache_result}))

    def send_and_listen(self, data):
        """encode given data before sending to remote server then parse returned result"""
        if not self.client:
            print("There is no connected client, try to restart proxy")
            return

        istring = json.dumps(data, cls=DataEncoder)
        self.client.send(istring)

        def listen_and_parse():
            result = self.client.receive()
            result = json.loads(result, cls=DataDecoder)
            if isinstance(result, Reference):
                result.set_proxy(self)
                raise TypeError("TEMP")
            return result

        result = listen_and_parse()
        # keep receiving response until a non-callback result is returned
        while True:
            if isinstance(result, dict):
                if 'callback' in result:
                    cb = result['callback']
                    self.callbacks[cb['id']](*cb['args'], **cb['kwargs'])
                    result = listen_and_parse()
                elif 'listen' in result:
                    print(*result['listen'])
                    result = listen_and_parse()
                else:
                    break
            else:
                break

        if isinstance(result, Payload):
            if result.type == 'error':
                raise ServerSideError("".join(result.content))
            return result.content
        else:
            raise ValueError("Unexpected payload: {}".format(result))

    def send_only(self, data):
        istring = json.dumps(data, cls=DataEncoder)
        return self.client.send(istring)

    def run(self, package, cache, *args, **kwargs):
        """pass the arguments to remote function and wait to receive the results"""
        args, kwargs = self.parse_callbacks(args, kwargs)
        idict = {'package': package, 'cache': cache,
                 'args': args, 'kwargs': kwargs}
        result = self.send_and_listen(idict)
        if isinstance(result, dict) and 'error' in result:
            raise ServerSideError("".join(result['error']))
        return result

    def Sessions(self, *args, **kwargs):
        return Sessions_client(self, *args, **kwargs)

    def get(self, cached_object: Reference):
        """get content of a cached object stored remotely"""
        return self.send_and_listen(Payload("get", cached_object))

    def cache(self, data, cached_id=None):
        """cache data or function to remote server and return a reference of it"""
        # if callable(data):
        #     idict = {'cache_func': {
        #         'name': data.__name__,
        #         'source': inspect.getsource(data)
        #     }, 'cached_id': cached_id}
        # else:
        #     idict = {'cache': data, 'cached_id': cached_id}
        # return self.send(idict)

        # TODO: deal with function
        return self.send_and_listen(Payload("cache", {"data": data, "cached_id": cached_id}))

    def parse_callbacks(self, args, kwargs):
        """replace a callback functions with its cached reference then sending it to server"""
        for i, a in enumerate(args):
            cb = a
            if callable(cb):
                args[i] = {'callback': {'id': id(cb)}}
                self.callbacks[id(cb)] = cb
        for key in kwargs:
            cb = kwargs[key]
            if callable(cb):
                kwargs[key] = {'callback': {'id': id(cb)}}
                self.callbacks[id(cb)] = cb
        return args, kwargs

    def try_reconnect(self):
        """try to reconnect to a existing server"""
        try:
            client = Client(self.host, self.port)
        except Exception:
            return None
        else:
            print("Reconnected to an existing server at {}:{}".format(self.host, self.port))
        return client

    def start_server(self):
        """use Popen to start a remote server in background"""
        env = compas._os.prepare_environment()

        args = [self._python, '-m', 'compas_cloud.server', '--port', str(self.port)]

        if self.background:
            print("Starting new cloud server in background at {}:{}".format(self.host, self.port))
            self._process = Popen(args, env=env)
        else:
            print("Starting new cloud server with prompt console at {}:{}".format(self.host, self.port))
            args[0] = compas._os.select_python('python')
            self._process = Popen(args, env=env)
        # import sys
        # self._process = Popen(args, stdout=sys.stdout, stderr=sys.stderr, env=env)

        success = False
        count = 20
        while count:
            if compas.IPY:
                Rhino.RhinoApp.Wait()
            try:
                time.sleep(0.2)
                client = Client(self.host, self.port)
            except Exception as e:

                if self._process.poll() is not None:
                    out, err = self._process.communicate()
                    if out:
                        print(out.decode())
                    if err:
                        raise RuntimeError(err.decode())
                    raise RuntimeError('subprocess terminated, reason unknown')

                count -= 1
                print(e)
                print("\n\n    {} attempts left.".format(count))
            else:
                success = True
                break
        if not success:
            raise RuntimeError("The server is not available.")
        else:
            print("server started with port", self.port)

        return client

    def restart(self):
        """shut down and restart existing server and given ip and port"""
        self.client = self.try_reconnect()
        self.shutdown()
        time.sleep(1)
        self.client = self.start_server()

    def shutdown(self):
        """shut down currently connected server"""
        if self.client:
            if self.send_only(Payload("control", "shutdown")):
                self.client = None
                print("server will shutdown and proxy client disconnected.")
        else:
            print("there is already no connected client")

    def check(self):
        """check if server connection is good"""
        return self.send_and_listen(Payload("control", "check"))

    def once(self):
        """Set the server to close once this client disconnet"""
        return self.send_and_listen(Payload("control", "once"))

    def version(self):
        """get version info of compas cloud server side packages"""
        return self.send_and_listen(Payload("control", "version"))

class Sessions_client():

    def __init__(self, proxy, *args, **kwargs):
        self.proxy = proxy
        idict = {'sessions': {'command': 'create', 'args': args, 'kwargs': kwargs}}
        print(self.proxy.send(idict))

    def start(self):
        idict = {'sessions': {'command': 'start', 'args': (), 'kwargs': {}}}
        print(self.proxy.send(idict))

    def add_task(self, func, *args, **kwargs):
        cached = self.proxy.cache(func)
        idict = {'sessions': {'command': 'add_task', 'func': cached, 'args': args, 'kwargs': kwargs}}
        print(self.proxy.send(idict))

    def listen(self):
        idict = {'sessions': {'command': 'listen', 'args': (), 'kwargs': {}}}
        print(self.proxy.send(idict))

    def terminate(self):
        pass


if __name__ == "__main__":
    pass
