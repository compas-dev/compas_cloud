from compas.data import Data


class CacheReference(Data):
    def __init__(self, cache_id=None):
        super(CacheReference, self).__init__()
        self.cache_id = cache_id
        self.proxy = None

    def set_proxy(self, proxy):
        self.proxy = proxy

    def get(self):
        pass

    def call(self, function_name, *args, cache=False, **kwargs):
        return self.proxy.call(self, function_name,*args, cache=cache, **kwargs)

    @property
    def data(self):
        return {"cache_id": self.cache_id}

    @data.setter
    def data(self, data):
        self.cache_id = data["cache_id"]

class TestClass(Data):
    def __init__(self, x=0):
        super(TestClass, self).__init__()
        self.x = x
    
    def __repr__(self) -> str:
        return f"TestClass(x={self.x})"

    def increment_x(self):
        self.x += 1
        print("x is now", self.x)

    @property
    def data(self):
        return {"x": self.x}

    @data.setter
    def data(self, data):
        self.x = data["x"]
