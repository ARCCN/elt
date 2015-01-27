class Message(object):
    """
    Base class for server interaction messages.
    """

    def __init__(self):
        self._name = str(self.__class__).rsplit('.', 1)[1][:-2]

    @property
    def name(self):
        return self._name

    def __setstate__(self, d):
        self._name = d.get("_name", self._name)

    def __getstate__(self):
        return {"_name": self._name}


class ClosingMessage(Message):
    pass
