import code
import sys

from ..database import *


class CLI:
    def __init__(self):
        self.db = DatabaseClient(mode='rw')

    def run(self):
        """
        Create hello message.
        """
        l = dict(globals())
        l.update({
            'db': self.db,
            'cli': self,
            'help_elt': self.help_elt
            })
        hello = '\nWelcome to ErrorLocalizationTool.\n'
        hello += 'Use db.find_flow_mod(dpid, match, actions)\n'
        hello += '\tmatch =   of.ofp_match()\n'
        hello += '\tmatch:    dl_src, dl_dst, dl_type, dl_vlan, dl_vlan_pcp\n'
        hello += '\t          nw_src, nw_dst, nw_proto, nw_tos\n'
        hello += '\t          tp_src, tp_dst, in_port\n'
        hello += '\tactions = [of.ofp_action_X()]\n'
        hello += '\tX:        dl_addr, enqueue, nw_addr, nw_tos, output,\n'
        hello += '\t          strip_vlan, tp_port, vendor_generic,\n'
        hello += '\t          vlan_pcp, vlan_vid\n'

        hello += '\tdpid =    int()\n'
        hello += 'See pox.openflow.libopenflow_01.py\n'
        hello += 'Use help_elt() for more information\n'
        return (hello, l)

    def help_elt(self):
        """
        Create help message.
        """
        h = "You can find following functions useful:\n"
        h += "\teth_to_int(EthAddr)\n\tint_to_eth(int)\n"
        h += "\tip_to_uint(IPAddr)\n\tuint_to_ip(uint)\n"
        h += "Module 'of' has a lot of useful stuff\n"
        h += "Use dir(of)\n\n"
        h += "Maintaining the connection:\n"
        h += "\tdb.reconnect()   Try to connect to DB.\n"
        h += "\tdb.close()       Stop DB server.\n"
        print h


if __name__ == '__main__':
    cli = CLI()
    sys.ps1 = 'POX_ELT>'
    sys.ps2 = '...'
    hello, l = cli.run()
    code.interact(hello, local=l)
