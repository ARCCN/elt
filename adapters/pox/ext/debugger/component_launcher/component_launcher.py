from __future__ import print_function

import sys
import traceback
import inspect
import types
from ConfigParser import ConfigParser
import os
from functools import partial

from pox.boot import _do_imports
from pox.core import core, ComponentRegistered
from pox.lib.revent.revent import EventHalt


log = core.getLogger("ComponentLauncher")
CONFIG = ["debugger/component_launcher/component_config/",
          "ext/debugger/component_launcher/component_config/",
          "pox/ext/debugger/component_launcher/component_config/",
          "adapters/pox/ext/debugger/component_launcher/component_config/"]
HIGHEST_PRIORITY = 0xffffffff


class CaseConfigParser(ConfigParser):
    def __init__(self, allow_no_value=False):
        ConfigParser.__init__(self, allow_no_value=allow_no_value)
        self.optionxform = str


class ComponentLauncher(object):
    def __init__(self, registered=[]):
        self.config = {} # {component_name: CaseConfigParser()}
        self.event_queue = {} # {target: {event_name: [events]}}
        self.tmp_queue = {}
        self.my_handlers = {} # {target: {event_name: [(4-tuple)]}}
        self.halt_events = False # True -> tmp_queue & halt.
                                 # False -> event_queue
        self.launched = [] # We do not support multiload.
                           # Multiple launch is error.
        self.now_launching = None

        self._read_config()
        # The only module whose launch we might miss.
        core.call_when_ready(self._openflow_handler, ["openflow"])
        # TODO: Maybe we should wait for other module like this?
        self._set_listeners() # Look through configs and listen to necessary events.
        self._set_listeners_to_registered(registered) # Some components
        self._add_registered(registered) # are already loaded. We listened!
        core.addListener(ComponentRegistered, self._handle_ComponentRegistered)

    def launch_single(self, argv):
        """
        Launch 1 module. Example: argv = ["openflow.of_01", "--port=3366"].
        The instantiated module will get the previous events from its config.
        """
        argv = self._preprocess(argv)
        components = [arg for arg in argv if not arg.startswith("-")]
        self._check_components(components)
        old_handlers = self._grab_handlers(components[0])
        self.now_launching = components[0]
        result = launch_all(argv)
        self.now_launching = None
        self.launched.append(components[0])
        # Subscribe on events for launched module.
        self._set_listeners_to_source(components[0])
        if result is False:
            return result
        new_handlers = self._grab_handlers(components[0])
        # We must continue listen to events while handlers are reset.
        # After our hack we must raise all events
        # that were missed by removed handlers.
        target_handlers = self._subtract_handlers(new_handlers, old_handlers)
        # Copy queue structure.
        self.tmp_queue = {a: {b: [] for b in self.event_queue[a]}
                          for a in self.event_queue}
        # Now we halt all events using our highest priority.
        # We store them to tmp_queue.
        self.halt_events = True
        # We feed the previous messages to newly created components.
        # log.debug(str(target_handlers))
        self._set_handlers(target_handlers)
        self._raise_events(target_handlers, self.event_queue)
        # We restore handlers and stop halting events.
        self._set_handlers(new_handlers)
        self.halt_events = False
        # We copy missed events to main queue.
        for section in self.tmp_queue:
            for event_name, events in self.tmp_queue[section].items():
                self.event_queue[section][event_name].extend(events)
        # Now we feed missed events to everyone.
        self._raise_events(new_handlers, self.tmp_queue)

    def launch_hierarchical(self, argv):
        """
        Launch component's dependency hierarchy using default params.
        If a dependency is already launched, skip it.
        After everything is loaded, load target component (strictly 1).
        """
        # TODO: Process default args.
        argv = self._preprocess(argv)
        components = [arg for arg in argv if not arg.startswith("-")]
        self._check_components(components)
        try:
            cp = self.config[components[0]]
            # Launch dependencies.
            for section in cp.sections():
                for component, cfg in self.config.items():
                    try:
                        if (cfg.get("self", "name") == section and
                                component not in self.launched):
                            # We found dependency.
                            arg = [component]
                            for k, v in cfg.defaults():
                                if v is None:
                                    arg.append(k)
                                else:
                                    arg.append("%s=%s" % (k, v))
                            self.launch_hierarchical(arg)
                            self.launched.append(component)
                    except Exception as e:
                        log.info(str(e))
                        continue
        except:
            pass
        # Now all known dependencies must be loaded.
        # We can load our target.
        log.info("Launching %s" % components[0])
        print("Launching %s" % components[0])
        sys.stdout.flush()
        self.launch_single(argv)

    def _handle_ComponentRegistered(self, event):
        if self._belongsToComponent(self.now_launching, "core." + event.name):
            return
        # TODO: Maybe more string workaround double-registration?
        self._set_listeners_to_registered([event])
        self._add_registered([event])

    def _belongsToComponent(self, component, name):
        """
        Checks whether this module contains this core_name.
        """
        if component is None or name is None:
            return False
        cp = self.config.get(component)
        try:
            if cp.get("self", "name") == name:
                return True
        except Exception as e:
            pass
        return False

    def _check_components(self, components):
        if len(components) != 1:
            raise ValueError("The number of component must be 1, not %d" %
                    len(components))
        if components[0] in self.launched:
            raise ValueError("%s is already launched. Cancel." % components[0])

    def _read_config(self):
        """
        Read config files from CONFIG. Files must be
        CONFIG[i]/*.cfg.
        """
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
                        cp = CaseConfigParser(allow_no_value=True)
                        log.info("Read config: %s" %
                                 cp.read(os.path.join(dirname, filename)))
                        self.config[filename.replace(".cfg", "")] = cp
            except Exception as e:
                pass

    def _set_listeners(self):
        """
        Subscribe to events from all config files.
        """
        for cp in self.config.values():
            for section in cp.sections():
                if section == "self":
                    continue
                try:
                    event_source = eval(section)
                    if section not in self.event_queue:
                        self.event_queue[section] = {}
                    if section not in self.my_handlers:
                        self.my_handlers[section] = {}
                    for event_name, module in cp.items(section):
                        self._import_and_listen(section, event_source,
                                                event_name, module)
                except Exception as e:
                    log.debug(str(e))

    def _set_listeners_to_source(self, component):
        """
        Given a module, listen to instances from this module.
        Module -> name from config.
        """
        # We must take the name of component instance.
        # Then look through configs to find out
        # who wants its messages.
        cp = self.config.get(component)
        section = None
        try:
            section = cp.get("self", "name")
        except:
            log.info("Unable to find instance of %s" % component)
            # We don't know how to find component instance.
            return
        for cp in self.config.values():
            try:
                event_source = eval(section)
                if not cp.has_section(section):
                    continue
                # Can these two be already set?
                if section not in self.event_queue:
                    self.event_queue[section] = {}
                if section not in self.my_handlers:
                    self.my_handlers[section] = {}
                for event_name, module in cp.items(section):
                    self._import_and_listen(section, event_source,
                                            event_name, module)
            except Exception as e:
                log.info(str(e))

    def _set_listeners_to_registered(self, registered):
        for event in registered:
            # We have instance names and instances.
            for cp in self.config.values():
                try:
                    section = "core." + event.name
                    event_source = event.component
                    if not cp.has_section(section):
                        continue
                    # Can these two be already set?
                    if section not in self.event_queue:
                        self.event_queue[section] = {}
                    if section not in self.my_handlers:
                        self.my_handlers[section] = {}
                    for event_name, module in cp.items(section):
                        self._import_and_listen(section, event_source,
                                                event_name, module)
                except Exception as e:
                    log.info(str(e))

    def _set_listeners_to_openflow(self):
        for cp in self.config.values():
            try:
                section = "core.openflow"
                event_source = eval(section)
                if not cp.has_section(section):
                    continue
                # Can these two be already set?
                if section not in self.event_queue:
                    self.event_queue[section] = {}
                if section not in self.my_handlers:
                    self.my_handlers[section] = {}
                for event_name, module in cp.items(section):
                    self._import_and_listen(section, event_source,
                                            event_name, module)
            except Exception as e:
                log.info(str(e))

    def _import_and_listen(self, section, event_source, event_name, module):
        """
        Import event class named "event_name" from "module".
        Subscribe to this event of event_source object.
        """
        try:
            # Maybe we are already listening?
            h = self.my_handlers[section][event_name]
            q = self.event_queue[section][event_name]
            if h is not None and q is not None:
                return
        except:
            pass
        _temp = __import__(module, fromlist=[event_name])
        globals()[event_name] = _temp.__dict__[event_name]
        h = partial(self._enqueue_event, section, event_name)
        self.my_handlers[section][event_name] = h
        self.event_queue[section][event_name] = []
        event_source.addListener(eval(event_name), h,
            priority=HIGHEST_PRIORITY)

    def _add_registered(self, registered):
        for event in registered:
            section = "core." + event.name
            for component, cfg in self.config.items():
                try:
                    # TODO: Not in launched?
                    if (cfg.get("self", "name") == section and
                           component not in self.launched):
                        self.launched.append(component)
                        print("Launched %s" % component)
                        log.info("Component %s already registered" % component)
                        sys.stdout.flush()
                except Exception as e:
                    log.info(str(e))
                    continue

    def _openflow_handler(self):
        self._set_listeners_to_openflow()
        self._add_openflow()

    def _add_openflow(self):
        section = "core.openflow"
        for component, cfg in self.config.items():
            try:
                # TODO: Not in launched?
                if (cfg.get("self", "name") == section and
                       component not in self.launched):
                    self.launched.append(component)
                    print("Launched %s" % component)
                    log.info("Component %s already registered" % component)
                    sys.stdout.flush()
            except Exception as e:
                log.info(str(e))
                continue


    def _enqueue_event(self, section, event_name, event):
        """
        If halt -> tmp_queue and return EventHalt.
        Otherwise -> event_queue.
        """
        # TODO: Maximum queue size.
        if event not in self.event_queue[section][event_name]:
            if self.halt_events:
                self.tmp_queue[section][event_name].append(event)
                return EventHalt
            self.event_queue[section][event_name].append(event)

    def _grab_handlers(self, component):
        """
        Copy and return the handlers from events wanted be component.
        """
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

    def _subtract_handlers(self, new, old):
        """
        return new[i][j] \ old[i][j]. (unique handlers of new)
        If the subtraction result is not empty (handlers changed)
        we explicitly add our handlers that were removed.
        """
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

    def _set_handlers(self, handlers):
        """
        Change the handlers to given structure.
        handlers = {object_name: {event_name: [handler]}}
        """
        for section in handlers:
            try:
                event_source = eval(section)
                for event_name, hlist in handlers[section].items():
                    event_source._eventMixin_handlers[eval(event_name)] = hlist
            except:
                pass
        return True

    def _raise_events(self, handlers, event_queue):
        """
        Raise events for handlers using event_queue.
        """
        for section in handlers:
            try:
                event_source = eval(section)
                for event_name in handlers[section]:
                    for event in event_queue[section][event_name]:
                        event_source.raiseEventNoErrors(event)
            except:
                pass
        return True

    def _preprocess(self, argv):
        """
        We allow strings w/o list.
        """
        if isinstance(argv, basestring):
            return [argv]
        argv = [x.strip() for x in argv if len(x.strip()) > 0]
        return argv


# This function is stolen from pox/boot.py
def launch_all (argv):
  component_order = []
  components = {}

  # Looks like we don't need pox args here.
  curargs = {}

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

  modules = _do_imports(n.split(':')[0] for n in component_order)
  if modules is False:
    return False

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

