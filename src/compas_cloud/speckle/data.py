from specklepy.objects import Base
from compas.data import json_dumps
import json


class Data(Base):
    data = dict

    def __init__(self, data={}, stream_id=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.data = json.loads(json_dumps(data))
        if stream_id:
            self.data['stream_id'] = stream_id
