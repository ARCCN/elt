from ext.debugger.elt.logger import LogClient
from ext.debugger.elt.network_error import NetworkError, Entry, EntryGroup
import pox.openflow.libopenflow_01 as of
from pox.openflow.of_01 import unpackers

class PolicyViolation(NetworkError):
    def __init__(self, ofp, dpid):
        NetworkError.__init__(self)
        self.desc = "Verifier policy violation"
        entries = [Entry(ofp, dpid)]
        self.entry_groups.append(EntryGroup("Faulty rule", entries=entries))


class Adapter(object):
    def __init__(self):
        self.log = LogClient("verifier_adapter")

    def _handle_ErrorIn(self, event):
        if (event.type != of.OFPET_FLOW_MOD_FAILED or
                event.code != of.OFPFMFC_ERERM):
            return

        # from openflow.of_01

        buf = event.ofp
        offset = 0
        ofp_type = ord(buf[offset+1])
        if ord(self.buf[offset]) != of.OFP_VERSION:
            if ofp_type == of.OFPT_HELLO:
            # We let this through and hope the other side switches down.
            pass
        else:
            log.warning("Bad OpenFlow version (0x%02x) on connection %s"
                      % (ord(buf[offset]), event.connection))
            return False # Throw connection away

        _,ofp = unpackers[ofp_type](self.buf, offset)

        if ofp_type == of.OFPT_FLOW_MOD:
            error = PolicyViolation(ofp, event.dpid)
            self.log.log_event(error)

