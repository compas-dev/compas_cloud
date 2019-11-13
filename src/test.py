from compas.geometry import Translation
from compas.geometry import transform_points
import time

import compas_cloud
proxy = compas_cloud.Proxy()
transform_points_numpy = proxy.package('compas.geometry.transform_points_numpy')



pts = []
for i in range(0, 1000):
    pts.append([i, 0, 0])

T = Translation([100, 0, 0]).matrix


# USING NATIVE PYTHON

start = time.time()

transformed = transform_points(pts, T)

end = time.time()

print('transform 1 million points(native python): ', end - start, 's')




# USING CLOUD WITH NUMPY

start = time.time()
transformed = transform_points_numpy(pts, T)
end = time.time()

print('transform 1 million points(cloud numpy): ', end - start, 's')
