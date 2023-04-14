from compas_cloud import Proxy
from compas_cloud.cache import TestClass


p = Proxy()

my_object = TestClass(1)
print(my_object)

my_object.increment_x()
print(my_object)

cached = p.cache(my_object)
print(cached)

for i in range(10):
    cached.call('increment_x')

my_object = p.get(cached)
print(my_object)
