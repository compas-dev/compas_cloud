from compas.data import Data


class Payload(Data):
    def __init__(self, type=None, content=None):
        super(Payload, self).__init__()
        self.type = type
        self.content = content
    
    def __repr__(self) -> str:
        return f"Payload(type={self.type}, content={self.content})"

    @property
    def __data__(self):
        return {"type": self.type, "content": self.content}
