class Message(object):
    """
    Base class for server interaction messages.
    """

    def __init__(self):
        self._name = str(self.__class__).rsplit('.', 1)[1][:-2]

    def __setstate__(self, d):
        pass


class ClosingMessage(Message):
    pass
