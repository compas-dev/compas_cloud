from compas.geometry import Translation
from compas.geometry import transform_points
import time
from compas_rhino.utilities import unload_modules
unload_modules("compas_cloud")


# USING NATIVE PYTHON


pts = [[i, 0, 0] for i in range(0, 10000)]
T = Translation([100, 0, 0]).matrix

start = time.time()

for i in range(0, 100):
    pts = transform_points(pts, T)

result1 = pts

end = time.time()
print('transform 10k points 100 times (native python): ', end - start, 's')



# USING CLOUD WITH CACHE

import compas_cloud
proxy = compas_cloud.Proxy_Net()
transform_points_numpy = proxy.package('compas.geometry.transform_points_numpy', cache=True)


pts = [[i, 0, 0] for i in range(0, 10000)]
T = Translation([100, 0, 0]).matrix

start = time.time()

pts = proxy.cache(pts)

for i in range(0, 100):
    pts = transform_points_numpy(pts, T)

result2 = proxy.get(pts)

end = time.time()
print('transform 10k points 100 times (cloud numpy): ', end - start, 's')

assert result1 == result2
