import json
import collections


name_to_class = {}


def controller_message(cls):
    if hasattr(cls, "_name"):
        name_to_class[cls._name] = cls
    return cls


def _get_dict(obj):
    """
    Call __getstate__ or simply return __dict__.
    """
    if hasattr(obj, "__getstate__"):
        r = obj.__getstate__()
    else:
        r = obj.__dict__
    return r


def _instantiate(d):
    if "_name" not in d:
        return d
    cls = name_to_class[d["_name"]]
    inst = cls()
    inst.__setstate__(d)
    return inst


def load_message(s):
    return json.loads(s, object_hook=_instantiate)


def dump_message(msg):
    if isinstance(msg, ControllerMessage):
        return msg.dumps()
    try:
        return json.dumps(msg, default=_get_dict)
    except:
        return json.dumps(str(msg))


@controller_message
class ControllerMessage(object):
    _name = "controller_message"

    def __init__(self):
        pass

    def __getstate__(self):
        d = self.__dict__.copy()
        d["_name"] = self._name
        return d

    def __setstate__(self, d):
        pass

    def dumps(self):
        return json.dumps(self, default=_get_dict)


@controller_message
class ControllerStatus(ControllerMessage):
    _name = "controller_status"

    def __init__(self, status="no_data"):
        self.status = status

    def __setstate__(self, d):
        self.status = d.get("status", self.status)


@controller_message
class GetControllerComponents(ControllerMessage):
    _name = "get_controller_components"


@controller_message
class StartController(ControllerMessage):
    _name = "start_controller"

    def __init__(self, args=""):
        self.args = args

    def __setstate__(self, d):
        self.args = d.get("args", self.args)


@controller_message
class StopController(ControllerMessage):
    _name = "stop_controller"


@controller_message
class LaunchComponent(ControllerMessage):
    _name = "launch_component"

    def __init__(self, component=None, args=None):
        self.component = component
        if args is None:
            args = []
        self.args = args

    def __setstate__(self, d):
        self.component = None
        self.args = []
        if "component" not in d:
            return
        self.component = d["component"]
        if "args" not in d or d["args"] is None:
            return
        try:
            for arg in d["args"]:
                self.args.append(arg)
        except:
            self.args.append(d["args"])

    def __str__(self):
        return self._name + " " + self.component + " " + " ".join(self.args)


@controller_message
class LaunchSingle(LaunchComponent):
    _name = "launch_single"


@controller_message
class LaunchHierarchical(LaunchComponent):
    _name = "launch_hierarchical"


class ComponentParam(object):
    def __init__(self, name="", has_default=False, default=None):
        self.name = name
        self.has_default = has_default
        self.default = default

    def __setstate__(self, d):
        if "name" not in d:
            return
        self.name = d["name"]
        self.has_default = d.get("has_default", self.has_default)
        self.default = d.get("default", self.default)


class Component(object):
    def __init__(self, name="", params=None):
        self.name = name
        if params is None:
            params = []
        self.params = params

    def __setstate__(self, d):
        if "name" not in d:
            return
        self.name = d["name"]
        try:
            for param in d["params"]:
                p = ComponentParam()
                p.__setstate__(param)
                self.params.append(p)
        except:
            pass


@controller_message
class ControllerComponents(ControllerMessage):
    _name = "controller_components"

    def __init__(self):
        self.components = []

    def add_component(self, component):
        self.components.append(component)

    def __setstate__(self, d):
        if "components" not in d:
            return
        try:
            for component in d["components"]:
                c = Component()
                c.__setstate__(component)
                self.components.append(c)
        except:
            pass


@controller_message
class ComponentLaunched(ControllerMessage):
    _name = "component_launched"

    def __init__(self, component=""):
        self.component = component

    def __setstate__(self, d):
        self.component = d.get("component", self.component)
