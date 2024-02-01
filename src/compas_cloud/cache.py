from compas.data import Data


class Reference(Data):

    proxy = None

    def __init__(self, cache_id=None):
        super(Reference, self).__init__()
        self.cache_id = cache_id

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(cache_id={self.cache_id})"

    @property
    def __data__(self):
        return {"cache_id": self.cache_id}


class FunctionReference(Reference):
    def __init__(self, cache_id=None, function_name=None, cache_result=False):
        super(FunctionReference, self).__init__(cache_id=cache_id)
        self.function_name = function_name
        self.cache_result = cache_result

    def __repr__(self) -> str:
        return f"FunctionReference(cache_id={self.cache_id}, function_name={self.function_name})"

    @property
    def __data__(self):
        return {
            "cache_id": self.cache_id,
            "function_name": self.function_name,
            "cache_result": self.cache_result,
        }

    def __call__(self, *args, **kwargs):
        return self.proxy.call(self, *args, **kwargs)


class ObjectReference(Reference):
    pass


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
    def __data__(self):
        return {"x": self.x}
