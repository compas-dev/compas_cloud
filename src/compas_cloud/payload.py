from compas.data import Data


class Payload(Data):
    def __init__(self, type=None, content=None):
        super(Payload, self).__init__()
        self.type = type
        self.content = content
    
    def __repr__(self) -> str:
        return f"Payload(type={self.type}, content={self.content})"

    @property
    def data(self):
        return {"type": self.type, "content": self.content}

    @data.setter
    def data(self, data):
        self.type = data["type"]
        self.content = data["content"]
