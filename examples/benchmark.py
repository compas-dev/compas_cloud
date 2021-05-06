from compas.geometry import Translation
from compas.geometry import transform_points
import time


# USING NATIVE PYTHON


pts = [[i, 0, 0] for i in range(0, 10000)]
T = Translation.from_vector([100, 0, 0])

start = time.time()

for i in range(0, 100):
    pts = transform_points(pts, T)

result1 = pts

end = time.time()
print('transform 10k points 100 times (native python): ', end - start, 's')



# USING CLOUD WITH CACHE

from compas_cloud import Proxy
proxy = Proxy(port=9001)
transform_points_numpy = proxy.function('compas.geometry.transform_points_numpy', cache=True)


pts = [[i, 0, 0] for i in range(0, 10000)]
T = Translation.from_vector([100, 0, 0])

start = time.time()

pts = proxy.cache(pts)

for i in range(0, 100):
    pts = transform_points_numpy(pts, T)

result2 = proxy.get(pts)

end = time.time()
print('transform 10k points 100 times (cloud numpy): ', end - start, 's')

assert result1 == result2
