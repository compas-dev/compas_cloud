from compas_cloud import Proxy
from compas.geometry import Translation


proxy = Proxy()
transform_points_numpy = proxy.package('compas.geometry.transform_points_numpy')
# create a proxy funciton

pts = [[0,0,0], [1,0,0]]
T = Translation([100, 0, 0]).matrix
result = transform_points_numpy(pts, T) # call the function through proxy
print(result)
# will print: [[100.0, 0.0 ,0.0], [101.0, 0.0, 0.0]]