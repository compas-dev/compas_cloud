from compas_cloud import Proxy
import time
proxy = Proxy()
dot = proxy.package('numpy.dot')

a = [[1, 0], [0, 1]]
b = [[4, 1], [2, 2]]
print(dot(a, b))
