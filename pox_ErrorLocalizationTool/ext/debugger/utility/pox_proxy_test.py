from ext.debugger.elt.database import *

d = Database()
match = of.ofp_match()
match.in_port=117
match.dl_src = int_to_eth(143473599782361)
match.dl_dst = int_to_eth(55360562547368)
match.dl_vlan = 65535
match.dl_vlan_pcp = 0
match.dl_type = 2048
match.nw_tos = 0
match.nw_proto = 1
match.nw_src = uint_to_ip(167772277)
match.nw_dst = uint_to_ip(167772252)
match.tp_src = 8
match.tp_dst = 0
print match
actions = []
actions.append(of.ofp_action_output(port=92))
#actions.append(of.ofp_action_output(port=93))
#actions.append(of.ofp_action_output(port=185))
d.find_flow_mod(match, actions, 1)

