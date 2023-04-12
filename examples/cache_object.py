from compas_cloud import Proxy
from compas.data import Data

class MyClass(Data):
    def __init__(self, x = 0):
        super(MyClass, self).__init__()
        self.x = x
    
    def increment_x(self):
        self.x += 1

    @property
    def data(self):
        return {'x': self.x}

    @data.setter
    def data(self, data):
        self.x = data['x']

    def __str__(self):
        return "MyClass(x={})".format(self.x)


p = Proxy()

my_object = MyClass(1)
print(my_object)

my_object.increment_x()
print(my_object)


my_object_ref = p.cache(my_object)
print(my_object_ref)