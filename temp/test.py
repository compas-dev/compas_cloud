from compas_cloud.proxy import Proxy

p = Proxy(speckle={"host": "speckle.xyz", "token": "__YOUR_TOKEN__"})
p.speckle.watch([stream1, stream2, stream3])
