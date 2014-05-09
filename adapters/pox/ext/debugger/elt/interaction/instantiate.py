import sys

from ..util import app_logging


log = app_logging.getLogger("Instantiate")


class Instantiator(object):
    def __init__(self, module=__name__, cls_param='_name'):
        self.module = module
        self.cls_param = cls_param

    def __call__(self, d):
        return instantiate(d, self.module, self.cls_param)


def instantiate(d, module=__name__, cls_param='_name'):
    obj = None
    try:
        c = d[cls_param]
        cls = getattr(sys.modules[module], c)
        obj = cls()
        del d[cls_param]
    except:
        return d
    if hasattr(obj, "__setstate__"):
        obj.__setstate__(d)
    else:
        for k, v in d.items():
            setattr(obj, k, v)
    return obj
