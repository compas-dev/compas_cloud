from compas_cloud import Proxy
from compas.geometry import Translation

# CACHING INPUT PARAMETERS

proxy = Proxy()
transform_points_numpy = proxy.package('compas.geometry.transform_points_numpy')
# create a proxy funciton

pts = [[0,0,0], [1,0,0]]
pts_cache = proxy.cache(pts) # cache the object to server side and return its reference
print(pts_cache) # will print: {'cached': some_unique_id}

T = Translation([100, 0, 0]).matrix
result = transform_points_numpy(pts_cache, T) # call the function through proxy
print(result) # will print: [[100.0, 0.0 ,0.0], [101.0, 0.0, 0.0]]



# CACHING RETURNED DATA

transform_points_numpy = proxy.package('compas.geometry.transform_points_numpy', cache=True)
# this function will now return a cache object instead of the actual data

pts = [[0,0,0], [1,0,0]]
pts_cache = proxy.cache(pts)
print(pts_cache) # will print: {'cached': some_unique_id}

T = Translation([100, 0, 0]).matrix
result_cache = transform_points_numpy(pts_cache, T) # call the function through proxy
print(result_cache) # will print: {'cached': some_unique_id}

result = proxy.get(result_cache) # fetch the actual data of the cache object
print(result) # will print: [[100.0, 0.0 ,0.0], [101.0, 0.0, 0.0]]