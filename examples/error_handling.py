from compas_cloud import Proxy
import time
proxy = Proxy()
dot = proxy.package('numpy.dot')

a = [[1, 0], [0, 1]]
b = [['a']]
dot(a, b)
"""
This should raise an error:
Exception: ValueError:shapes (2,2) and (1,1) not aligned: 2 (dim 1) != 1 (dim 0)
"""
