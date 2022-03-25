from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
from specklepy.transports.server import ServerTransport
from specklepy.api import operations
from data import Data as SpeckleData
from compas.data import json_loads
import json


class Speckle():
    def __init__(self, host="speckle.xyz", token=None):
        self.client = SpeckleClient(host=host)
        account = get_account_from_token(token, host)
        self.client.authenticate_with_account(account)

    def update_item(self, item, stream_id=None, name=None, message=None):
        # Create new stream if stream_id is None
        if not stream_id:
            stream_id = self.client.stream.create(name=name)
        transport = ServerTransport(client=self.client, stream_id=stream_id)
        hash = operations.send(base=SpeckleData(item), transports=[transport])
        self.client.commit.create(
            stream_id=stream_id,
            object_id=hash,
            message=message,
        )
        return stream_id

    def get_item(self, stream_id):
        stream = self.client.stream.get(id=stream_id)
        transport = ServerTransport(client=self.client, stream_id=stream_id)
        latest_commit = stream.branches.items[0].commits.items[0]
        received_base = operations.receive(obj_id=latest_commit.referencedObject, remote_transport=transport)
        data = received_base.data
        return json_loads(json.dumps(data))


if __name__ == "__main__":

    import compas
    from compas.datastructures import Mesh

    client = Speckle(token="5da18a1e41f477bf4d70bce651b151aa6e14d5cc8d")

    stream_id = "c0538fd521"
    # mesh = Mesh.from_obj(compas.get('faces.obj'))
    # stream_id = client.update_item(mesh, name="faces", stream_id=stream_id)
    # print(stream_id)

    # stream_id = "c0538fd521"
    item = client.get_item(stream_id)
    print(item)
