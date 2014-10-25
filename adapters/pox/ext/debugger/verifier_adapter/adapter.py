from ext.debugger.elt.logger import LogClient
from ext.debugger.elt.network_error import NetworkError, Entry, EntryGroup
import pox.openflow.libopenflow_01 as of
from pox.openflow.of_01 import unpackers
from pox.core import core
from ext.debugger.elt.interaction import ofp_flow_mod


log = core.getLogger("VerifierAdapter")


class Policy(object):
    def __init__(self, buf=None):
        self.buf = buf

    def __str__(self):
        if self.buf == "" or self.buf is None:
            return "n/d"
        return str(self.buf)


class PolicyViolation(NetworkError):
    def __init__(self, ofp, dpid, policy):
        NetworkError.__init__(self)
        self.desc = "Verifier policy: %s" % str(policy)
        entries = [Entry(ofp_flow_mod.from_flow_mod(ofp), dpid)]
        self.entry_groups.append(EntryGroup("Faulty rule", entries=entries))


class Adapter(object):
    _core_name = "verifier_adapter"

    def __init__(self):
        self.log = LogClient("verifier_adapter")

    def _handle_ErrorIn(self, event):
        if (event.ofp.type != of.OFPET_FLOW_MOD_FAILED or
                event.ofp.code != of.ofp_flow_mod_failed_code_rev_map[
                    "OFPFMFC_EPERM"]):
            return

        event.should_log = False
        # from openflow.of_01

        buf = event.ofp.data
        offset = 0
        ofp_type = ord(buf[offset+1])
        if ord(buf[offset]) != of.OFP_VERSION:
            if ofp_type == of.OFPT_HELLO:
                # We let this through and hope the other side switches down.
                pass
            else:
                log.warning("Bad OpenFlow version (0x%02x) on connection %s against 0x02x"
                        % (ord(buf[offset]), event.connection, of.OFP_VERSION))
            	return False # Throw connection away

        offset,ofp = unpackers[ofp_type](buf, offset)
        policy = Policy(buf[offset:])

        if ofp_type == of.OFPT_FLOW_MOD:
            error = PolicyViolation(ofp, event.dpid, policy)
            self.log.log_event(error)


