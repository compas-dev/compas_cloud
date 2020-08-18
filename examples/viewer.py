from compas_cloud import Proxy
import compas
from compas.datastructures import Mesh


m = Mesh.from_ply(compas.get_bunny())


p = Proxy()

result = p.send({
    "viewer":{
        "draw": {
            "uuid": "uuid1234",
            "data": m.to_data()
        }
    }
    })

print(result)