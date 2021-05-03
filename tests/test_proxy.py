from compas_cloud import Proxy
from compas.geometry import Translation
from compas.geometry import allclose
import time
import pytest

PROXY = None


@pytest.fixture
def proxy():
    global PROXY
    if not PROXY:
        PROXY = Proxy(background=True)
    return PROXY


def test_basic(proxy):
    transform_points_numpy = proxy.function('compas.geometry.transform_points_numpy')
    pts = [[0, 0, 0], [1, 0, 0]]
    T = Translation.from_vector([100, 0, 0])
    result = transform_points_numpy(pts, T)
    assert allclose(result, [[100, 0, 0], [101, 0, 0]])


def test_cached(proxy):

    transform_points_numpy = proxy.function('compas.geometry.transform_points_numpy')

    pts = [[0,0,0], [1,0,0]]
    pts_cache = proxy.cache(pts) # cache the object to server side and return its reference
    print(pts_cache) # will print: {'cached': some_unique_id}

    T = Translation().from_vector([100, 0, 0])
    result = transform_points_numpy(pts_cache, T) # call the function through proxy
    print(result) # will print: [[100.0, 0.0 ,0.0], [101.0, 0.0, 0.0]]
    assert allclose(result, [[100, 0, 0], [101, 0, 0]])


    # CACHING RETURNED DATA

    transform_points_numpy = proxy.function('compas.geometry.transform_points_numpy', cache=True)
    # this function will now return a cache object instead of the actual data

    pts = [[0,0,0], [1,0,0]]
    pts_cache = proxy.cache(pts)
    print(pts_cache) # will print: {'cached': some_unique_id}

    T = Translation().from_vector([100, 0, 0])
    result_cache = transform_points_numpy(pts_cache, T) # call the function through proxy
    print(result_cache) # will print: {'cached': some_unique_id}

    result = proxy.get(result_cache) # fetch the actual data of the cache object
    print(result) # will print: [[100.0, 0.0 ,0.0], [101.0, 0.0, 0.0]]
    assert allclose(result, [[100, 0, 0], [101, 0, 0]])


def test_server_control(proxy):

    print(proxy.check())

    print("\n restarting the background server and open a new one in a prompt console")
    proxy.restart()
    time.sleep(0.5)

    print("\n check if the proxy is healthily connected to server")
    print(proxy.check())
    time.sleep(0.5)

    print("\n shut the the server and quite the program")
    proxy.shutdown()
    time.sleep(3)
