from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import json

from compas.utilities import DataEncoder
from compas.utilities import DataDecoder

import compas
import os

import time
import inspect

from subprocess import Popen
from subprocess import PIPE

if compas.IPY:
    from .client_net import Client_Net as Client
    import Rhino
else:
    from .client_websockets import Client_Websokets as Client


__all__ = ['Proxy']

from functools import wraps
def retry_if_exception(ex, max_retries, wait = 0):
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
                    print('proxy call failed, trying time left:',x)
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
        Default is ``9000``.

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

    def __init__(self, host='127.0.0.1', port=9000, background=True, errorHandler=None):
        """init function that starts a remote server then assigns corresponding client(websockets/.net) to the proxy"""
        self._python = compas._os.select_python(None)
        self.host = host
        self.port = port
        self.background = background
        self.client = self.try_reconnect()
        if not self.client:
            self.client = self.start_server()
        self.callbacks = {}
        self.errorHandler = errorHandler

    def package(self, function, cache=False):
        raise RuntimeError("Proxy.package() has been deprecated, please use Proxy.function() instead.")
        

    def function(self, function, cache=False):
        """returns wrapper of function that will be executed on server side"""

        if self.errorHandler:
            @self.errorHandler
            @retry_if_exception(Exception, 5, wait = 0.5)
            def run_function(*args, **kwargs):
                return self.run(function, cache, *args, **kwargs)

            return run_function
        else:
            @retry_if_exception(Exception, 5, wait = 0.5)
            def run_function(*args, **kwargs):
                return self.run(function, cache, *args, **kwargs)
            
            return run_function

    def send(self, data):
        """encode given data before sending to remote server then parse returned result"""
        if not self.client:
            print("There is no connected client, try to restart proxy")
            return
        
        istring = json.dumps(data, cls=DataEncoder)
        self.client.send(istring)

        def listen_and_parse():
            result = self.client.receive()
            return json.loads(result, cls=DataDecoder)

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

        return result

    def send_only(self, data):
        istring = json.dumps(data, cls=DataEncoder)
        return self.client.send(istring)

    def run(self, package, cache, *args, **kwargs):
        """pass the arguments to remote function and wait to receive the results"""
        args, kwargs = self.parse_callbacks(args, kwargs)
        idict = {'package': package, 'cache': cache,
                 'args': args, 'kwargs': kwargs}
        result = self.send(idict)
        if 'error' in result:
            raise ServerSideError("".join(result['error']))
        return result

    def Sessions(self, *args, **kwargs):
        return Sessions_client(self, *args, **kwargs)

    def get(self, cached_object):
        """get content of a cached object stored remotely"""
        idict = {'get': cached_object['cached']}
        return self.send(idict)

    def cache(self, data):
        """cache data or function to remote server and return a reference of it"""
        if callable(data):
            idict = {'cache_func': {
                'name': data.__name__,
                'source': inspect.getsource(data)
            }}
        else:
            idict = {'cache': data}
        return self.send(idict)

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

        args = [self._python, '-m', 'compas_cloud.server', str(self.port)]

        if self.background:
            print("Starting new cloud server in background at {}:{}".format(self.host, self.port))
            self._process = Popen(args, stdout=PIPE, stderr=PIPE, env=env)
        else:
            print("Starting new cloud server with prompt console at {}:{}".format(self.host, self.port))
            args[0] = compas._os.select_python('python')
            args = " ".join(args)
            os.system('start '+args)
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

                # stop trying if the subprocess is not running anymore
                if self.background:
                    if self._process.poll() is not None:
                        out, err =  self._process.communicate()
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
            if self.send_only({'control': 'shutdown'}):
                self.client = None
                print("server will shutdown and proxy client disconnected.")
        else:
            print("there is already no connected client")

    def check(self):
        """check if server connection is good"""
        return self.send({'control': 'check'})


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
