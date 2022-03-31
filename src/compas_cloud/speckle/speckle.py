from specklepy.api.client import SpeckleClient
from specklepy.api.credentials import get_account_from_token
from specklepy.transports.server import ServerTransport
from specklepy.api import operations
from compas_cloud.speckle.data import Data as SpeckleData
from compas.data import json_loads
import json


class Speckle():

    def process_command(self, command):
        if 'connect' in command:
            return self.connect(host=command['connect']['host'], token=command['connect']['token'])
        if 'get' in command:
            return self.get_item(command['get']['stream_id'])
        if 'update' in command:
            return self.update_item(command['update']['item'], stream_id=command['update']['stream_id'])
        else:
            return "Command not found"

    def connect(self, host="speckle.xyz", token=None):
        print("Connecting to {} with {}".format(host, token))
        self.client = SpeckleClient(host=host)
        account = get_account_from_token(token, host)
        self.client.authenticate_with_account(account)
        return "Connected"

    def update_item(self, item, stream_id=None, name=None, message=None):
        print("CHECK!", item)
        print("CHECK!", stream_id)
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

    # def watch_item(self, stream_id, callback):
    #     item = self.get_item(stream_id)
    #     callback(item)

if __name__ == "__main__":

    import compas
    from compas.datastructures import Mesh

    client = Speckle()
    client.connect(token="4b6a06f4c7b114e3b4115e1bba5536261cb4d3bf20")

    stream_id = "c0538fd521"
    mesh = Mesh.from_obj(compas.get('faces.obj'))
    stream_id = client.update_item(mesh, name="faces", stream_id=stream_id)
    print(stream_id)

    # stream_id = "c0538fd521"
    # item = client.get_item(stream_id)
    # print(item)
