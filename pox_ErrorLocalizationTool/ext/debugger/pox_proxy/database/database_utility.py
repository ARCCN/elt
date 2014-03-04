# This file contains functions to make CREATE, SELECT, INSERT queries
# to different database tables.
# TODO: Maybe create subclasses for each table/query type?

from collections import namedtuple
import time

from pox.lib.addresses import EthAddr, IPAddr
import pox.openflow.libopenflow_01 as of

from ..util import eth_to_int, int_to_eth, ip_to_uint, uint_to_ip

TableColumn = namedtuple('TableColumn', 'name type attr')

# Lists of table headers, types and additional attributes.

FlowMatch = []
FlowMatch.append(
    TableColumn("ID", "INT UNSIGNED", "PRIMARY KEY AUTO_INCREMENT"))
FlowMatch.append(TableColumn("wildcards", "INT UNSIGNED", "NOT NULL"))
FlowMatch.append(TableColumn("in_port", "SMALLINT UNSIGNED", ""))
FlowMatch.append(TableColumn("dl_src", "BIGINT UNSIGNED", ""))
FlowMatch.append(TableColumn("dl_dst", "BIGINT UNSIGNED", ""))
FlowMatch.append(TableColumn("dl_vlan", "SMALLINT UNSIGNED", ""))
FlowMatch.append(TableColumn("dl_vlan_pcp", "TINYINT UNSIGNED", ""))
FlowMatch.append(TableColumn("dl_type", "SMALLINT UNSIGNED", ""))
FlowMatch.append(TableColumn("nw_tos", "TINYINT UNSIGNED", ""))
FlowMatch.append(TableColumn("nw_proto", "TINYINT UNSIGNED", ""))
FlowMatch.append(TableColumn("nw_src", "INT UNSIGNED", ""))
FlowMatch.append(TableColumn("nw_dst", "INT UNSIGNED", ""))
FlowMatch.append(TableColumn("tp_src", "SMALLINT UNSIGNED", ""))
FlowMatch.append(TableColumn("tp_dst", "SMALLINT UNSIGNED", ""))

FlowModParams = []
FlowModParams.append(
    TableColumn("ID", "INT UNSIGNED", "PRIMARY KEY AUTO_INCREMENT"))
FlowModParams.append(TableColumn("command", "SMALLINT UNSIGNED", "NOT NULL"))
FlowModParams.append(TableColumn("idle_timeout", "SMALLINT UNSIGNED", ""))
FlowModParams.append(TableColumn("hard_timeout", "SMALLINT UNSIGNED", ""))
FlowModParams.append(TableColumn("priority", "SMALLINT UNSIGNED", "NOT NULL"))
FlowModParams.append(TableColumn("buffer_id", "INT UNSIGNED", ""))
FlowModParams.append(TableColumn("out_port", "SMALLINT UNSIGNED", ""))
FlowModParams.append(TableColumn("flags", "SMALLINT UNSIGNED", ""))

Actions = []
Actions.append(TableColumn("ID", "INT UNSIGNED", "PRIMARY KEY AUTO_INCREMENT"))
Actions.append(TableColumn("type", "SMALLINT UNSIGNED", "NOT NULL"))
Actions.append(TableColumn("port", "SMALLINT UNSIGNED", "NOT NULL"))
Actions.append(TableColumn("value", "BIGINT UNSIGNED", "NOT NULL"))

ActionPatterns = []
ActionPatterns.append(
    TableColumn("ID", "INT UNSIGNED", "PRIMARY KEY AUTO_INCREMENT"))

ActionPatternsToActions = []
ActionPatternsToActions.append(TableColumn("ID", "INT UNSIGNED",
                                           "PRIMARY KEY AUTO_INCREMENT"))
ActionPatternsToActions.append(
    TableColumn("actionpat_ID", "INT UNSIGNED", "NOT NULL"))
ActionPatternsToActions.append(
    TableColumn("action_ID", "INT UNSIGNED", "NOT NULL"))


CodeEntries = []
CodeEntries.append(
    TableColumn("ID", "INT UNSIGNED", "PRIMARY KEY AUTO_INCREMENT"))
CodeEntries.append(TableColumn("line", "INT UNSIGNED", "NOT NULL"))
CodeEntries.append(TableColumn("module", "VARCHAR(400)", "NOT NULL"))

CodePatterns = []
CodePatterns.append(
    TableColumn("ID", "INT UNSIGNED", "PRIMARY KEY AUTO_INCREMENT"))

CodePatternsToCodeEntries = []
CodePatternsToCodeEntries.append(TableColumn("ID", "INT UNSIGNED",
                                             "PRIMARY KEY AUTO_INCREMENT"))
CodePatternsToCodeEntries.append(
    TableColumn("codepat_ID", "INT UNSIGNED", "NOT NULL"))
CodePatternsToCodeEntries.append(
    TableColumn("codeentry_ID", "INT UNSIGNED", "NOT NULL"))

FlowMods = []
FlowMods.append(
    TableColumn("ID", "INT UNSIGNED", "PRIMARY KEY AUTO_INCREMENT"))
FlowMods.append(TableColumn("match_ID", "INT UNSIGNED", "NOT NULL"))
FlowMods.append(TableColumn("params_ID", "INT UNSIGNED", "NOT NULL"))
FlowMods.append(TableColumn("dpid", "BIGINT", "NOT NULL"))
FlowMods.append(TableColumn("actionpat_ID", "INT UNSIGNED", ""))
FlowMods.append(TableColumn("codepat_ID", "INT UNSIGNED", ""))
FlowMods.append(TableColumn("time", "DATETIME", ""))

tables = {}
#tables["FlowMatchCopy"] = FlowMatch
tables["FlowMatch"] = FlowMatch
tables["FlowModParams"] = FlowModParams
tables["Actions"] = Actions
tables["ActionPatterns"] = ActionPatterns
tables["ActionPatternsToActions"] = ActionPatternsToActions
tables["CodeEntries"] = CodeEntries
tables["CodePatterns"] = CodePatterns
tables["CodePatternsToCodeEntries"] = CodePatternsToCodeEntries
tables["FlowMods"] = FlowMods

TableFunctions = namedtuple(
    "TableFunctions", "add insert select convert_insert")

functions = {}


#-----------------------------------Common------------------------------------


def create_table(name):
    if name not in tables:
        return ""
    query = "CREATE TABLE IF NOT EXISTS " + name + " ("
    for column in tables[name]:
        query += column.name + ' ' + column.type + ' ' + column.attr + ', '
    query = query[:-2] + ');'
    return query


def add_complex(table_name, arg, out_var=None, args=None):
    l = [] if args is not None else None
    queries = []
    queries.append("SET @var=NULL; ")
    queries.append(functions[table_name].select(arg, fields="ID",
                                                var="@var", args=l))
    queries.append("; SELECT @var;")
    queries.append(functions[table_name].insert(arg, ignore=True,
                                                id_var="@var", args=l))
    if out_var:
        queries.append(" SET ")
        queries.append(out_var)
        queries.append(" = (SELECT CASE WHEN @var IS NULL THEN ")
        queries.append("(SELECT LAST_INSERT_ID()) ELSE @var END);\n")
    else:
        queries.append(" SELECT CASE WHEN @var IS NULL THEN ")
        queries.append("(SELECT LAST_INSERT_ID()) ELSE @var END;\n")
    query = "".join(queries)
    if args is not None:
        args.extend(l)
    else:
        pass
    return query


# Common look of INSERT statements.
# Uses custom argument format function for each table.
def insert_table(table_name, return_last_id=False, ignore=False, id_var=None,
                 out_var=None, args=None, *arg):
    queries = []
    queries.append("INSERT ")
    if ignore:
        queries.append(" IGNORE ")
    queries.append("INTO ")
    queries.append(table_name)
    queries.append(" (")
    for column in tables[table_name]:
        if column.name != "ID" or id_var is not None:
            queries.append(column.name)
            queries.append(', ')
    query = "".join(queries)
    queries = []
    query = query[:-2]
    queries.append(") VALUES (")
    if id_var is not None:
        queries.append(str(id_var))
        if len(arg) > 0:
            queries.append(", ")
    queries.append(functions[table_name].convert_insert(*arg, args=args))
    queries.append(");")
    if return_last_id:
        queries.append(" SELECT LAST_INSERT_ID();\n")
    if out_var:
        queries.append(" SET ")
        queries.append(out_var)
        queries.append(" = (SELECT LAST_INSERT_ID());\n")
    query += "".join(queries)
    return query


#-----------------------------------Table-Specific---------------------------

# FlowMatch table

def create_flow_match():
    cr = create_table("FlowMatch")
    cr = cr[:-2] + ", UNIQUE INDEX flow ("
    for column in tables["FlowMatch"]:
        if column.name != "ID":
            cr += column.name + ", "
    cr += "ID" + ", "
    cr = cr[:-2] + ") ) ENGINE = InnoDB;"
    # print cr
    return cr


def add_flow_match(match):
    return add_complex("FlowMatch", match)


def insert_flow_match(match, return_last_id=False, ignore=False,
                      id_var=None, out_var=None, args=None):
    return insert_table("FlowMatch", return_last_id, ignore,
                        id_var, out_var, args, match)


def select_flow_match(match, fields='*', var=None, args=None):
    queries = []
    queries.append("SELECT ")
    queries.append(fields)
    if var:
        queries.append(" INTO ")
        queries.append(str(var))
    queries.append(" FROM FlowMatch WHERE ")
    for column in tables["FlowMatch"]:
        if column.name != "ID":
            queries.append(column.name)
            queries.append(" <=> %s AND ")
    query = "".join(queries)[:-5] + " LIMIT 1 "
    l = (match.wildcards, match.in_port, eth_to_int(match.dl_src),
         eth_to_int(match.dl_dst), match.dl_vlan, match.dl_vlan_pcp,
         match.dl_type,
         match.nw_tos, match.nw_proto, ip_to_uint(match.nw_src),
         ip_to_uint(match.nw_dst), match.tp_src, match.tp_dst)
    if args is not None:
        args.extend(l)
    else:
        l = tuple([(a if a is not None else 'NULL') for a in l])
        query = query % l
    return query


def convert_insert_flow_match(match, args=None):
    l = (match.wildcards, match.in_port, eth_to_int(match.dl_src),
         eth_to_int(match.dl_dst), match.dl_vlan, match.dl_vlan_pcp,
         match.dl_type, match.nw_tos, match.nw_proto,
         ip_to_uint(match.nw_src), ip_to_uint(match.nw_dst),
         match.tp_src, match.tp_dst)
    q = "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s"
    if args is not None:
        args.extend(l)
    else:
        l = tuple([(a if a is not None else 'NULL') for a in l])
        q = q % l
    return q

# FlowModParams table


def create_flow_mod_params():
    cr = create_table("FlowModParams")
    cr = cr[:-2] + ", INDEX params (command, priority))"
    cr += " ENGINE = MyISAM;"
    # print cr
    return cr


def add_flow_mod_params(flow_mod):
    return add_complex("FlowModParams", flow_mod)


def insert_flow_mod_params(flow_mod, return_last_id=False, ignore=False,
                           id_var=None, out_var=None, args=None):
    return insert_table("FlowModParams", return_last_id, ignore,
                        id_var, out_var, args, flow_mod)


def select_flow_mod_params(flow_mod, fields='*', var=None, args=None):
    query = "SELECT " + fields
    if var:
        query += " INTO " + str(var)
    query += " FROM FlowModParams WHERE "
    for column in tables["FlowModParams"]:
        if column.name != "ID":
            query += column.name + " <=> %s AND "
    query = query[:-5]
    l = (flow_mod.command, flow_mod.idle_timeout,
         flow_mod.hard_timeout, flow_mod.priority,
         # flow_mod.buffer_id,
         None, flow_mod.out_port, flow_mod.flags)
    #l = tuple([(a if a is not None else 'NULL') for a in l])
    #query = query.replace("= None", " IS NULL")
    if args is not None:
        args.extend(l)
    else:
        l = tuple([(a if a is not None else 'NULL') for a in l])
        query = query % l
    return query


def convert_insert_flow_mod_params(flow_mod, args=None):
    l = (flow_mod.command, flow_mod.idle_timeout, flow_mod.hard_timeout,
         flow_mod.priority, None,  # flow_mod.buffer_id
         flow_mod.out_port,
         flow_mod.flags)
    q = "%s, %s, %s, %s, %s, %s, %s"
    #l = tuple([(a if a is not None else 'NULL') for a in l])

    if args is not None:
        args.extend(l)
    else:
        l = tuple([(a if a is not None else 'NULL') for a in l])
        q = q % l
    return q

# Actions table


def create_actions():
    cr = create_table("Actions")
    cr = cr[:-2] + ", UNIQUE INDEX action ("
    for column in tables["Actions"]:
        if column.name != "ID":
            cr += column.name + ", "
    cr = cr[:-2] + ") ) ENGINE = MyISAM;"
    # print cr
    return cr


def add_actions(action):
    return add_complex("Actions", action)


def get_action_params(action):
    type = action.type
    port = 0
    value = 0
    if isinstance(action, of.ofp_action_output):
        port = action.port
    elif isinstance(action, of.ofp_action_enqueue):
        port = action.port
        value = action.queue_id
    elif isinstance(action, of.ofp_action_strip_vlan):
        pass
    elif isinstance(action, of.ofp_action_vlan_vid):
        value = action.vlan_vid
    elif isinstance(action, of.ofp_action_vlan_pcp):
        value = action.vlan_pcp
    elif isinstance(action, of.ofp_action_dl_addr):
        value = eth_to_int(action.dl_addr)
    elif isinstance(action, of.ofp_action_nw_addr):
        value = ip_to_uint(action.nw_addr)
    elif isinstance(action, of.ofp_action_nw_tos):
        value = action.nw_tos
    elif isinstance(action, of.ofp_action_tp_port):
        value = action.tp_port
    elif isinstance(action, of.ofp_action_vendor_generic):
        value = action.vendor
    return (type, port, value)


def insert_actions(action, return_last_id=False, ignore=False,
                   id_var=None, out_var=None, args=None):
    return insert_table("Actions", return_last_id, ignore,
                        id_var, out_var, args, action)


def select_actions(action, fields='*', var=None, args=None):
    query = "SELECT " + fields
    if var:
        query += " INTO " + str(var)
    query += " FROM Actions WHERE "
    for column in tables["Actions"]:
        if column.name != "ID":
            query += column.name + " = %s AND "
    query = query[:-5]
    l = get_action_params(action)
    #l = tuple([(a if a is not None else 'NULL') for a in l])
    if args is not None:
        args.extend(l)
    else:
        l = tuple([(a if a is not None else 'NULL') for a in l])
        query = query % l
    #query = query.replace("= None", " IS NULL")
    return query


def convert_insert_actions(action, args=None):
    q = "%s, %s, %s"
    l = get_action_params(action)
    #l = tuple([(a if a is not None else 'NULL') for a in l])

    if args is not None:
        args.extend(l)
    else:
        l = tuple([(a if a is not None else 'NULL') for a in l])
        q = q % l
    return q

# ActionPatterns table


def create_action_patterns():
    return create_table("ActionPatterns")[:-1] + " ENGINE = MyISAM;"


def add_action_patterns():
    return insert_action_patterns()


def insert_action_patterns(return_last_id=False, ignore=False,
                           id_var=None, out_var=None):
    return insert_table("ActionPatterns", return_last_id, ignore,
                        id_var, out_var)


def convert_insert_action_patterns(args=None):
    return ""

# ActionPatternsToActions table


def create_action_patterns_to_actions():
    return create_table("ActionPatternsToActions")[:-1] + " ENGINE = MyISAM;"


def add_action_patterns_to_actions(actionpat_ID, action_ID):
    return insert_action_patterns_to_actions(actionpat_ID, action_ID)


def insert_action_patterns_to_actions(
        actionpat_ID, action_ID, return_last_id=False,
        ignore=False, id_var=None, out_var=None):
    return insert_table("ActionPatternsToActions", return_last_id, ignore,
                        id_var, out_var, actionpat_ID, action_ID)


def select_action_patterns_to_actions(actionpat_ID, action_ID, fields='*',
                                      var=None, args=None):
    query = "SELECT " + fields + " FROM ActionPatternsToActions WHERE "
    for column in tables["ActionPatternsToActions"]:
        if column.name != "ID":
            query += column.name + " = %s AND "
    query = query[:-5]
    l = (actionpat_ID, action_ID)
    #l = tuple([(a if a is not None else 'NULL') for a in l])
    if args is not None:
        args.extend(l)
    else:
        l = tuple([(a if a is not None else 'NULL') for a in l])
        query = query % l
    #query = query.replace("= None", " IS NULL")
    return query


def convert_insert_action_patterns_to_actions(actionpat_ID,
                                              action_ID, args=None):
    q = "%s, %s"
    l = (actionpat_ID, action_ID)
    #l = tuple([(a if a is not None else 'NULL') for a in l])
    if args is not None:
        args.extend(l)
    else:
        l = tuple([(a if a is not None else 'NULL') for a in l])
        q = q % l
    return q


# CodeEntries table
def create_code_entries():
    cr = create_table("CodeEntries")
    cr = cr[:-2] + ", UNIQUE INDEX code_entry ("
    for column in tables["CodeEntries"]:
        if column.name != "ID":  # and column.name != 'module':
            cr += column.name + ", "
    cr = cr[:-2] + ") ) ENGINE = MyISAM;"
    # print cr
    return cr


def add_code_entries(code_entry):
    return add_complex("CodeEntries", code_entry)


def insert_code_entries(code_entry, return_last_id=False, ignore=False,
                        id_var=None, out_var=None, args=None):
    return insert_table("CodeEntries", return_last_id, ignore,
                        id_var, out_var, args, code_entry)


def select_code_entries(code_entry, fields='*', var=None, args=None):
    query = "SELECT " + fields
    if var:
        query += " INTO " + str(var)
    query += " FROM CodeEntries WHERE "
    for column in tables["CodeEntries"]:
        if column.name != "ID" and (column.name != "module"
                                    or args is not None):
            query += column.name + " = %s AND "
        elif column.name == "module" and args is None:
            query += column.name + " = \"%s\" AND "
    query = query[:-5]
    l = (code_entry[1], code_entry[0])
    #l = tuple([(a if a is not None else 'NULL') for a in l])
    if args is not None:
        args.extend(l)
    else:
        l = tuple([(a if a is not None else 'NULL') for a in l])
        query = query % l
    #query = query.replace("= None", " IS NULL")
    return query


def convert_insert_code_entries(code_entry, args=None):
    if args is None:
        q = "%s, \"%s\""
    else:
        q = "%s, %s"
    l = (code_entry[1], code_entry[0])
    #l = tuple([(a if a is not None else 'NULL') for a in l])

    if args is not None:
        args.extend(l)
    else:
        l = tuple([(a if a is not None else 'NULL') for a in l])
        q = q % l
    return q

# CodePatterns table


def create_code_patterns():
    return create_table("CodePatterns")[:-1] + " ENGINE = MyISAM;"


def add_code_patterns():
    return insert_code_patterns()


def insert_code_patterns(return_last_id=False, ignore=False,
                         id_var=None, out_var=None):
    return insert_table("CodePatterns", return_last_id, ignore,
                        id_var, out_var)


def convert_insert_code_patterns(args=None):
    return ""


# CodePatternsToCodeEntries table

def create_code_patterns_to_code_entries():
    return create_table("CodePatternsToCodeEntries")[:-1] + " ENGINE = MyISAM;"


def add_code_patterns_to_code_entries(codepat_ID, codeentry_ID):
    return insert_code_patterns_to_code_entries(codepat_ID, codeentry_ID)


def insert_code_patterns_to_code_entries(
        codepat_ID, codeentry_ID, return_last_id=False,
        ignore=False, id_var=None, out_var=None):
    return insert_table("CodePatternsToCodeEntries", return_last_id, ignore,
                        id_var, out_var, codepat_ID, codeentry_ID)


def select_code_patterns_to_code_entries(codepat_ID, codeentry_ID,
                                         fields='*', var=None, args=None):
    query = "SELECT " + fields + " FROM CodePatternsToCodeEntries WHERE "
    for column in tables["CodePatternsToCodeEntries"]:
        if column.name != "ID":
            query += column.name + " = %s AND "
    query = query[:-5]
    l = (codepat_ID, codeentry_ID)
    #l = tuple([(a if a is not None else 'NULL') for a in l])
    if args is not None:
        args.extend(l)
    else:
        l = tuple([(a if a is not None else 'NULL') for a in l])
        query = query % l
    #query = query.replace("= None", " IS NULL")
    return query


def convert_insert_code_patterns_to_code_entries(codepat_ID,
                                                 codeentry_ID, args=None):
    q = "%s, %s"
    l = (codepat_ID, codeentry_ID)
    #l = tuple([(a if a is not None else 'NULL') for a in l])

    if args is not None:
        args.extend(l)
    else:
        l = tuple([(a if a is not None else 'NULL') for a in l])
        q = q % l
    return q


# FlowMods table
def create_flow_mods():
    cr = create_table("FlowMods")
    '''
    cr = cr[:-2] + ", INDEX flow_entry (match_ID, dpid, actionpat_ID)"
    cr += ", INDEX (dpid, actionpat_ID, params_ID)"
    '''

    cr = cr[:-2] + (", INDEX (dpid, actionpat_ID, params_ID)"
                    ", INDEX (match_ID, dpid, actionpat_ID))"
                    " ENGINE = InnoDB;")
    return cr


def add_flow_mods(match_ID, params_ID, dpid, actionpat_ID,
                  codepat_ID, out_var=None):
    return insert_flow_mods(match_ID, params_ID, dpid, actionpat_ID,
                            codepat_ID, True)


def insert_flow_mods(match_ID, params_ID, dpid, actionpat_ID, codepat_ID,
                     return_last_id=False, ignore=False, id_var=None,
                     out_var=None, args=None):
    return insert_table("FlowMods", return_last_id, ignore,
                        id_var, out_var, args, match_ID, params_ID,
                        dpid, actionpat_ID, codepat_ID)


def select_flow_mods(match_ID, params_ID, dpid, actionpat_ID,
                     codepat_ID=None, fields='*'):
    query = "SELECT " + fields + " FROM FlowMods WHERE "
    for column in tables["FlowMods"]:
        if (column.name != 'time' and column.name != "ID" and
                column.name != 'codepat_ID'):
            query += column.name + " = %s AND "
    query = query[:-5] % (match_ID, params_ID, dpid, actionpat_ID)
    if codepat_ID is not None:
        query += ' AND codepat_ID = %s' % (codepat_ID)
    query = query.replace("= None", " IS NULL")
    return query


def convert_insert_flow_mods(match_ID, params_ID, dpid, actionpat_ID,
                             codepat_ID, args=None):
    q = "%s, %s, %s, %s, %s,\"%s\""
    l = (match_ID, params_ID, dpid, actionpat_ID,
         codepat_ID, time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()))

    if args is not None:
        args.extend(l)
    else:
        l = tuple([(a if a is not None else 'NULL') for a in l])
        q = q % l
    return q


# Function map

functions["FlowMatchCopy"] = TableFunctions(add_flow_match, insert_flow_match,
                                            select_flow_match,
                                            convert_insert_flow_match)
functions["FlowMatch"] = functions["FlowMatchCopy"]
functions["FlowModParams"] = TableFunctions(add_flow_mod_params,
                                            insert_flow_mod_params,
                                            select_flow_mod_params,
                                            convert_insert_flow_mod_params)
functions["Actions"] = TableFunctions(add_actions, insert_actions,
                                      select_actions, convert_insert_actions)
functions["ActionPatterns"] = TableFunctions(add_action_patterns,
                                             insert_action_patterns, None,
                                             convert_insert_action_patterns)
functions["ActionPatternsToActions"] = TableFunctions(
    add_action_patterns_to_actions,
    insert_action_patterns_to_actions,
    select_action_patterns_to_actions,
    convert_insert_action_patterns_to_actions)
functions["CodeEntries"] = TableFunctions(add_code_entries,
                                          insert_code_entries,
                                          select_code_entries,
                                          convert_insert_code_entries)
functions["CodePatterns"] = TableFunctions(add_code_patterns,
                                           insert_code_patterns, None,
                                           convert_insert_code_patterns)
functions["CodePatternsToCodeEntries"] = TableFunctions(
    add_code_patterns_to_code_entries,
    insert_code_patterns_to_code_entries,
    select_code_patterns_to_code_entries,
    convert_insert_code_patterns_to_code_entries)
functions["FlowMods"] = TableFunctions(add_flow_mods, insert_flow_mods,
                                       select_flow_mods,
                                       convert_insert_flow_mods)
