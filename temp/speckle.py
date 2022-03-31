import compas
from compas.datastructures import Mesh

from compas_cloud.proxy import Proxy

p = Proxy()
result = p.send({"speckle": {"connect": {"host": "speckle.xyz", "token": "4b6a06f4c7b114e3b4115e1bba5536261cb4d3bf20"}}})
print("check", result)

mesh = Mesh.from_obj(compas.get('faces.obj'))
# mesh = Mesh.from_off(compas.get('tubemesh.off'))


mesh = p.send({"speckle": {"update": {"stream_id": "c0538fd521", "item": mesh}}})
print(mesh)
