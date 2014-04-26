from __future__ import print_function
import code
import sys

from .database_client import DatabaseClient
from .database import Database


class CLI(object):
    def __init__(self):
        self.db_client = DatabaseClient(mode='rw', connect=False)
        self.db = Database()

    def run(self):
        """
        Create hello message.
        """
        l = dict(globals())
        l.update({
            'db': self.db,
            'db_client': self.db_client,
            'cli': self,
            'help_db': self.help_db
            })
        hello = '\nWelcome to ErrorLocalizationTool DbConsole.\n'
        hello += '\nDatabase Client : db_client\n'
        hello += '\tdb_client.reconnect() - try to connect to DB\n'
        hello += '\tdb_client.close() - stop DB server\n'
        hello += '\tdb_client.find_flow_mod(dpid, match, actions)\n'
        hello += 'See pox.openflow.libopenflow_01.py\n'
        hello += '\nDatabase : db\n'
        hello += '\tdb.clear() - Erase database\n'
        hello += '\tdb.drop_tables()\n'
        hello += '\tdb.create_tables()\n'
        hello += 'Use help_db() for more information\n'
        return (hello, l)

    def help_db(self):
        """
        Create help message.
        """
        h = 'db_client.find_flow_mod(dpid, match, actions)\n'
        h += '\tmatch =   of.ofp_match()\n'
        h += '\tmatch:    dl_src, dl_dst, dl_type, dl_vlan, dl_vlan_pcp\n'
        h += '\t          nw_src, nw_dst, nw_proto, nw_tos\n'
        h += '\t          tp_src, tp_dst, in_port\n'
        h += '\tactions = [of.ofp_action_X()]\n'
        h += '\tX:        dl_addr, enqueue, nw_addr, nw_tos, output,\n'
        h += '\t          strip_vlan, tp_port, vendor_generic,\n'
        h += '\t          vlan_pcp, vlan_vid\n'
        h += '\tdpid =    int()\n'

        h += "You can find following functions useful:\n"
        h += "\teth_to_int(EthAddr)\n\tint_to_eth(int)\n"
        h += "\tip_to_uint(IPAddr)\n\tuint_to_ip(uint)\n"
        h += "Module 'of' has a lot of useful stuff\n"
        h += "Use dir(of)\n\n"
        h += "Maintaining the connection:\n"
        h += "\tdb_client.reconnect()   Try to connect to DB.\n"
        h += "\tdb_client.close()       Stop DB server.\n"
        print(h)


def db_cli():
    cli = CLI()
    sys.ps1 = 'DB>'
    sys.ps2 = '...'
    hello, l = cli.run()
    code.interact(hello, local=l)


if __name__ == '__main__':
    main()
