from __future__ import print_function

import sys
import traceback
import inspect
import types
from ConfigParser import ConfigParser
import os
from functools import partial
import copy

from pox.boot import _do_imports
from pox.core import core
from pox.lib.revent.revent import EventHalt
from ext.debugger.elt.util import app_logging


log = app_logging.getLogger("ComponentLauncher")
CONFIG = ["debugger/component_launcher/component_config/",
          "ext/debugger/component_launcher/component_config/",
          "pox/ext/debugger/component_launcher/component_config/",
          "adapters/pox/ext/debugger/component_launcher/component_config/"]
HIGHEST_PRIORITY = 1000000


class CaseConfigParser(ConfigParser):
    def __init__(self):
        ConfigParser.__init__(self)
        self.optionxform = str


class ComponentLauncher(object):
    def __init__(self):
        self.argv = []
        self.config = {} # {component_name: CaseConfigParser()}
        self.event_queue = {}
        self.my_handlers = {}
        self.halt_events = False
        self.read_config()
        self.set_listeners()
        # core.openflow.addListeners(self)

    def read_config(self):
        def _raise(x):
            raise x

        for directory in CONFIG:
            try:
                for dirname, dirnames, filenames in os.walk(
                        directory, onerror=_raise):
                    del dirnames[:]
                    for filename in filenames:
                        if not filename.endswith(".cfg"):
                            continue
                        cp = CaseConfigParser()
                        log.info("Read config:",
                                 cp.read(os.path.join(dirname, filename)))
                        self.config[filename.replace(".cfg", "")] = cp
            except Exception as e:
                pass

    def set_listeners(self):
        for component, cp in self.config.items():
            for section in cp.sections():
                if section == "self":
                    continue
                try:
                    event_source = eval(section)
                    self.event_queue[section] = {}
                    self.my_handlers[section] = {}
                    for event_name, module in cp.items(section):
                        _temp = __import__(module, fromlist=[event_name])
                        globals()[event_name] = _temp.__dict__[event_name]
                        h = partial(self.enqueue_event, section, event_name)
                        event_source.addListener(eval(event_name), h,
                            priority=HIGHEST_PRIORITY)
                        self.my_handlers[section][event_name] = h
                        self.event_queue[section][event_name] = []
                except Exception as e:
                    log.info(str(e))

    def enqueue_event(self, section, event_name, event):
        # TODO: Maximum queue size.
        if event not in self.event_queue[section][event_name]:
            self.event_queue[section][event_name].append(event)
            if self.halt_events:
                return EventHalt

    def launch_single(self, argv):
        argv = self.preprocess(argv)
        # TODO: Subscribe on events for launched module.
        components = [arg for arg in argv if not arg.startswith("-")]
        if len(components) != 1:
            raise ValueError("The number of component must be 1, not %d" %
                    len(components))
        old_handlers = self.grab_handlers(components[0])
        result = launch_all(argv)
        if result is False:
            return result
        new_handlers = self.grab_handlers(components[0])
        print(old_handlers)
        print(new_handlers)
        # TODO: We must continue listen to events while handlers are reset.
        # TODO: After our hack we must raise all events
        # TODO: that were missed by removed handlers.
        target_handlers = self.subtract_handlers(new_handlers, old_handlers)
        # Now we halt all events using our highest priority.
        self.halt_events = True
        # We feed the previous messages to newly created components.
        print(target_handlers)
        self.set_handlers(components[0], target_handlers)
        self.raise_events(target_handlers)
        # We restore handlers and stop halting events.
        self.set_handlers(components[0], new_handlers)
        self.halt_events = False
        # Now we feed all the missed events to everyone.
        self.raise_events(new_handlers)

    def grab_handlers(self, component):
        handlers = {}
        cp = self.config.get(component)
        if cp is None:
            return handlers
        for section in cp.sections():
            if section == "self":
                continue
            try:
                event_source = eval(section)
                handlers[section] = {}
                for event_name, module in cp.items(section):
                    handlers[section][event_name] = event_source.\
                            _eventMixin_handlers.get(eval(event_name), [])[:]
            except:
                pass
        return handlers

    def subtract_handlers(self, new, old):
        # If the subtraction result is not empty (handlers changed)
        # we explicitly add our handlers that were removed.
        try:
            result = {}
            for section in new:
                res = {}
                for event_name in new[section]:
                    handlers = [h for h in new[section][event_name]
                                if h not in old[section][event_name]
                                or h[1] != self.my_handlers[section][
                                    event_name]]
                    # We are the only listener. Nothing changed -> ignore.
                    if (len(handlers) == 0 or (len(handlers) == 1 and
                            handlers[0][1] == self.my_handlers[
                                section][event_name])):
                        continue
                    res[event_name] = handlers
                if len(res) > 0:
                    result[section] = res
            return result
        except Exception as e:
            log.error(str(e))
            return {}

    def set_handlers(self, component, handlers):
        for section in handlers:
            try:
                event_source = eval(section)
                for event_name, hlist in handlers[section].items():
                    event_source._eventMixin_handlers[eval(event_name)] = hlist
            except:
                pass
        return True

    def raise_events(self, handlers):
        for section in handlers:
            try:
                event_source = eval(section)
                for event_name in handlers[section]:
                    for event in self.event_queue[section][event_name]:
                        event_source.raiseEventNoErrors(event)
            except:
                pass
        return True



    '''
    # Not compatible with message buffering.
    def enqueue(self, argv):
        self.argv.extend(self.preprocess(argv))

    def launch_queue(self):
        return launch_all(self.argv)
    '''

    def preprocess(self, argv):
        if isinstance(argv, basestring):
            return [argv]
        return argv


# This function is stolen from pox/boot.py
def launch_all (argv):
  component_order = []
  components = {}

  # Looks like we don't need pox args here.
  curargs = {}
  # pox_options = curargs

  for arg in argv:
    if not arg.startswith("-"):
      if arg not in components:
        components[arg] = []
      curargs = {}
      components[arg].append(curargs)
      component_order.append(arg)
    else:
      arg = arg.lstrip("-").split("=", 1)
      arg[0] = arg[0].replace("-", "_")
      if len(arg) == 1: arg.append(True)
      curargs[arg[0]] = arg[1]

  '''
  _options.process_options(pox_options)
  global core
  if pox.core.core is not None:
    core = pox.core.core
    core.getLogger('boot').debug('Using existing POX core')
  else:
    core = pox.core.initialize(_options.threaded_selecthub,
                               _options.epoll_selecthub,
                               _options.handle_signals)

  _pre_startup()
  '''

  modules = _do_imports(n.split(':')[0] for n in component_order)
  if modules is False:
    return False

  # TODO: Read necessery events for module from config. +
  # TODO: Save events to queue. +
  # TODO: Upon instantiation, save previous handlers from dependency. +
  # TODO: Instantiate module. +
  # TODO: Subtract handlers. +
  # TODO: Raise enqueued events from source to newly added handlers. +

  inst = {}
  for name in component_order:
    cname = name
    inst[name] = inst.get(name, -1) + 1
    params = components[name][inst[name]]
    name = name.split(":", 1)
    launch = name[1] if len(name) == 2 else "launch"
    name = name[0]

    name,module,members = modules[name]

    if launch in members:
      f = members[launch]
      # We explicitly test for a function and not an arbitrary callable
      if type(f) is not types.FunctionType:
        print(launch, "in", name, "isn't a function!")
        return False

      if getattr(f, '_pox_eval_args', False):
        import ast
        for k,v in params.items():
          if isinstance(v, str):
            try:
              params[k] = ast.literal_eval(v)
            except:
              # Leave it as a string
              pass

      multi = False
      if f.__code__.co_argcount > 0:
        #FIXME: This code doesn't look quite right to me and may be broken
        #       in some cases.  We should refactor to use inspect anyway,
        #       which should hopefully just fix it.
        if (f.__code__.co_varnames[f.__code__.co_argcount-1]
            == '__INSTANCE__'):
          # It's a multi-instance-aware component.

          multi = True

          # Special __INSTANCE__ paramter gets passed a tuple with:
          # 1. The number of this instance (0...n-1)
          # 2. The total number of instances for this module
          # 3. True if this is the last instance, False otherwise
          # The last is just a comparison between #1 and #2, but it's
          # convenient.
          params['__INSTANCE__'] = (inst[cname], len(components[cname]),
           inst[cname] + 1 == len(components[cname]))

      if multi == False and len(components[cname]) != 1:
        print(name, "does not accept multiple instances")
        return False

      try:
        if f(**params) is False:
          # Abort startup
          return False
      except TypeError as exc:
        instText = ''
        if inst[cname] > 0:
          instText = "instance {0} of ".format(inst[cname] + 1)
        print("Error executing {2}{0}.{1}:".format(name,launch,instText))
        if inspect.currentframe() is sys.exc_info()[2].tb_frame:
          # Error is with calling the function
          # Try to give some useful feedback
          # if _options.verbose:
          #   traceback.print_exc()
          # else:
          exc = sys.exc_info()[0:2]
          print(''.join(traceback.format_exception_only(*exc)), end='')


          print()
          EMPTY = "<Unspecified>"
          code = f.__code__
          argcount = code.co_argcount
          argnames = code.co_varnames[:argcount]
          defaults = list((f.func_defaults) or [])
          defaults = [EMPTY] * (argcount - len(defaults)) + defaults
          args = {}
          for n, a in enumerate(argnames):
            args[a] = [EMPTY,EMPTY]
            if n < len(defaults):
              args[a][0] = defaults[n]
            if a in params:
              args[a][1] = params[a]
              del params[a]
          if '__INSTANCE__' in args:
            del args['__INSTANCE__']

          if f.__doc__ is not None:
            print("Documentation for {0}:".format(name))
            doc = f.__doc__.split("\n")
            #TODO: only strip the same leading space as was on the first
            #      line
            doc = map(str.strip, doc)
            print('',("\n ".join(doc)).strip())

          #print(params)
          #print(args)

          print("Parameters for {0}:".format(name))
          if len(args) == 0:
            print(" None.")
          else:
            print(" {0:25} {1:25} {2:25}".format("Name", "Default",
                                                "Active"))
            print(" {0:25} {0:25} {0:25}".format("-" * 15))

            for k,v in args.iteritems():
              print(" {0:25} {1:25} {2:25}".format(k,str(v[0]),
                    str(v[1] if v[1] is not EMPTY else v[0])))

          if len(params):
            print("This component does not have a parameter named "
                  + "'{0}'.".format(params.keys()[0]))
            return False
          missing = [k for k,x in args.iteritems()
                     if x[1] is EMPTY and x[0] is EMPTY]
          if len(missing):
            print("You must specify a value for the '{0}' "
                  "parameter.".format(missing[0]))
            return False

          return False
        else:
          # Error is inside the function
          raise
    elif len(params) > 0 or launch is not "launch":
      print("Module %s has no %s(), but it was specified or passed " \
            "arguments" % (name, launch))
      return False

  return True

