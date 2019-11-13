from compas.geometry import Translation
from compas.geometry import transform_points
import time


pts = []
for i in range(0, 10000):
    pts.append([i, 0, 0])

T = Translation([100, 0, 0]).matrix



# # USING NATIVE PYTHON

start = time.time()
transformed = transform_points(pts, T)

for i in range(0, 100):
    transformed = transform_points(transformed, T)

t1 = transformed

end = time.time()
print('transform 10k points 100 times (native python): ', end - start, 's')



# USING CLOUD WITH CACHE

import compas_cloud
proxy = compas_cloud.Proxy()
transform_points_numpy = proxy.package('compas.geometry.transform_points_numpy', cache=True)

start = time.time()
transformed = transform_points_numpy(pts, T)

for i in range(0, 100):
    transformed = transform_points_numpy(transformed, T)

t2 = proxy.get(transformed)

end = time.time()
print('transform 10k points 100 times (cloud numpy): ', end - start, 's')

assert t1 == t2
