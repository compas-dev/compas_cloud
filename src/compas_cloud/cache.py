from compas.data import Data


class CacheReference(Data):
    def __init__(self, cache_id=None):
        super(CacheReference, self).__init__()
        self.cache_id = cache_id

    @property
    def data(self):
        return {"cache_id": self.cache_id}

    @data.setter
    def data(self, data):
        self.cache_id = data["cache_id"]
