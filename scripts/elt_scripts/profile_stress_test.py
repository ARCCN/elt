#!/usr/bin/python

"""
Process the profile records to readable statistics.
"""


from os import listdir
from os.path import isfile, join
import re
import pstats

mypath = "profile/"
onlyfiles = [ f for f in listdir(mypath) if isfile(join(mypath,f)) ]
file_keys = {}
m = re.compile(r"([A-Za-z_]*)(_[0-9]*_)?[0-9]*.prof")
for f in onlyfiles:
    try:
        key = m.match(f).group(1)
    except:
        print "error", f
        continue
    if len(key) == 0:
        continue
    if key not in file_keys:
        file_keys[key] = [join(mypath, f)]
    else:
        file_keys[key].append(join(mypath, f))

stats = {}
for f in file_keys:
    if len(file_keys[f]) == 0:
        continue
    # Need a hack because Stats.add() fails with long sequences.
    stats[f] = pstats.Stats(file_keys[f][0])
    for x in file_keys[f][1:]:
        try:
            stats[f].add(x)
        except Exception as e:
            print x, e

sections = {"Database": [("_save_data", "Message saving"),
                         ("_find_flow_mod", "Find message by fields"),
                         ("_find_rule", "Find messages for rule"),
                         ("show_code", "Find call stack for message")],
	    "Proxy": [("handle_PACKET_IN", "Total processing"),
                      ("save_info", "Proxy overhead"),
                      ("process_flow_mod", "Flow table overhead")],
	    "Flow table": [("add_entry_error_checking", "Rule addition"),
                           ("modify_error_checking", "Rule modification"),
                           ("delete_error_checking", "Rule deletion")]
	   }

try:
    print "Proxy"
    f = "handle_PACKET_IN"
    # How many packetIns we got.
    total_line = stats[f].stats[stats[f].eval_print_amount(f, stats[f].stats.keys(), "")[0][0]]
    #print "\t%-30s %.6f" % ("Total processing", total_line[3] / total_line[0])
    f = "save_info"
    # Response. OFP_FLOW_MOD.
    overhead_line = stats[f].stats[stats[f].eval_print_amount(f, stats[f].stats.keys(), "")[0][0]]
    #print "\t%-30s %.6f" % ("Proxy overhead", overhead_line[3] / overhead_line[0])
    f = "process_flow_mod"
    # Processing by flow table.
    table_line = stats[f].stats[stats[f].eval_print_amount(f, stats[f].stats.keys(), "")[0][0]]
    #print "\t%-30s %.6f" % ("Flow table overhead", table_line[3] / table_line[0])
    print "\t%-30s %.6f" % ("Total processing", (total_line[3] - table_line[3]) / total_line[0])
    print "\t%-30s %.6f" % ("Application time", (total_line[3] - overhead_line[3]) / total_line[0])
    print "\t%-30s %.6f" % ("Saving overhead", (overhead_line[3] - table_line[3]) / overhead_line[0])
except:
    pass


for s in sections:
    print "%s:" % s
    for f in sections[s]:
        try:
    	    line = stats[f[0]].stats[stats[f[0]].eval_print_amount(f[0], stats[f[0]].stats.keys(), "")[0][0]]
    	    print "\t%-30s %.6f" % (f[1], line[3] / line[0])
        except:
            pass


