import numbers
import socket
import MySQLdb as mdb
import MySQLdb.cursors

import pox.openflow.libopenflow_01 as of
from pox.lib.recoco.recoco import Exit

from ..message_server import Message, PythonMessageServer
from ..interaction import SimpleConnection, TimeoutException
from ..util import app_logging, profile, uint_to_ip, int_to_eth

from .database_utility import *
from .caches import *
from .messages import FlowModMessage, FlowModQuery, RuleQuery, QueryReply
from .query_creator import QueryCreator


# Database connection defaults.
USER = 'user'
DOMAIN = 'localhost'
PASSWORD = '1234'
DATABASE = 'POX_proxy'
#Logging
log = app_logging.getLogger("Database")
ENABLE_LOGGING = True


class LoggingCursor:
    def __init__(self, cur, log_file):
        self.cur = cur
        self.log_file = log_file

    def __getattr__(self, name):
        if name == "cur":
            return self.cur
        if name == "execute":
            return self.execute
        else:
            return getattr(self.cur, name)

    def __setattr__(self, name, value):
        if name == "cur":
            self.__dict__[name] = value
        elif name == "execute":
            self.__dict__[name] = value
        else:
            return setattr(self.cur, name, value)

    def execute(self, query, args=None):
        s = str(query)
        if s[-1] == ';':
            self.log_file.write(s + "\n")
        else:
            self.log_file.write(s + ";\n")
        #log_file.flush()
        return self.cur.execute(query, args)


class LoggingConnection:
    def __init__(self, con, log_file):
        self.con = con
        self.log_file = log_file

    def cursor(self):
        return LoggingCursor(self.con.cursor(), self.log_file)

    def close(self):
        self.con.close()


class Database:
    """
    Interacts with mysql server.
    Can process specific kinds of messages.
    """

    SIMPLE = 0
    DICTIONARY = 1

    def __init__(self, domain=DOMAIN, user=USER,
                 password=PASSWORD, table_name=DATABASE):
        self.user = user
        self.domain = domain
        self.password = password
        self.table_name = table_name
        self.connect()
        self.create_tables()
        self.tick_id = 0
        self.actions = ActionsCache()
        self.code_entries = CodeEntriesCache()
        self.action_patterns = ActionPatternsToActionsCache()
        self.code_patterns = CodePatternsToCodeEntriesCache()
        self.params = FlowModParamsCache()
        self.matches = FlowMatchCache()
        self._closing = False

# Public interfaces

    def connect(self):
        try:
            self.con = mdb.connect(self.domain, self.user,
                                   self.password, self.table_name)
            if ENABLE_LOGGING:
                log_file = open("queries.log", "w")
                self.con = LoggingConnection(self.con, log_file)
        except:
            self._closing = True

    def create_tables(self):
        if self.con:
            cur = self.con.cursor()
            cur._defer_warnings = True
            cur.execute(create_flow_match())
            cur.execute(create_flow_mod_params())
            cur.execute(create_actions())
            cur.execute(create_action_patterns())
            cur.execute(create_action_patterns_to_actions())
            cur.execute(create_code_entries())
            cur.execute(create_code_patterns())
            cur.execute(create_code_patterns_to_code_entries())
            cur.execute(create_flow_mods())
            cur.execute("set autocommit=ON;")
            cur.execute("show variables like \'autocommit\';")
            log.info(str(cur.fetchall()))
            cur.execute("show variables like \'%flush_log_at_trx%\';")
            log.info(str(cur.fetchall()))
            cur.execute("show variables like \'profiling\';")
            log.info(str(cur.fetchall()))

    def __del__(self):
        try:
            self.disconnect()
        except:
            pass

    def disconnect(self):
        if self.con:
            self.con.close()
            self.con = None

    def flush_stats(self):
        f = open('Database.stats', 'w')
        caches = [self.actions, self.code_entries, self.action_patterns,
                  self.code_patterns, self.params, self.matches]
        for cache in caches:
            f.write("%07d hit : %07d miss, %s\n" % (
                cache.hit, cache.miss, cache.__class__))
        f.close()

    def clear(self):
        """
        Remove all data from the tables.
        """
        if self.con:
            cur = self.con.cursor()
            try:
                for table in tables.keys():
                    cur.execute("DELETE FROM " + table)
            except:
                pass

    def drop_tables(self):
        """
        Remove all tables used.
        """
        if self.con:
            cur = self.con.cursor()
            try:
                for table in tables.keys():
                    cur.execute("DROP TABLE " + table)
            except:
                pass

    def flush_buffer(self, queue):
        """
        One cycle of flushing. Add BUFFER_SIZE or lesser messages to base.
        @return True    flushing successful.
                False   buffer empty.
                None    not connected.
        """
        if self.con and len(queue) > 0:
            self.tick_id += 1
            results = []
            # More complex strategy with caching
            for q in queue:
                result = self.process_message(q)
                if result is not None:
                    results.append(result)
            return results
        elif not self.con:
            return None
        return False

    def show_code(self, id):
        """
        Return call stack for FlowMod with ID.
        """
        if id is None:
            return 'Not found'
        if self.con:
            query = ("SELECT module, line FROM CodeEntries JOIN "
                     "CodePatternsToCodeEntries ON CodeEntries.ID = "
                     "CodePatternsToCodeEntries.codeentry_ID JOIN "
                     "FlowMods on FlowMods.codepat_ID = "
                     "CodePatternsToCodeEntries.codepat_ID AND "
                     "FlowMods.ID = %s order by "
                     "CodePatternsToCodeEntries.ID;") % (id)
            cur = self.con.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            while cur.nextset() is not None:
                rows = cur.fetchall()
            return rows

    def process_message(self, message):
        """
        Save FlowMod data, respond queries.
        """
        if not isinstance(message, Message):
            return None
        if isinstance(message, FlowModMessage):
            try:
                return self._save_data(message)
            except Exception as e:
                log.debug(str(e))
                return e
        elif (isinstance(message, FlowModQuery) or
              isinstance(message, RuleQuery)):
            try:
                return self._reply_query(message)
            except Exception as e:
                log.debug(str(e))
                return e
        return None

    def _reply_query(self, message):
        """
        Assert parameter types.
        Return (call_stack, qid).
        """
        if not isinstance(message.data.match, of.ofp_match):
            raise TypeError("Match is not instance of ofp_match")
        for a in message.data.actions:
            if not isinstance(a, of.ofp_action_base):
                raise TypeError("Action is not instance of ofp_action_base")
        if not isinstance(message.dpid, numbers.Integral):
            raise TypeError("DPID is not Integral")
        if not isinstance(message.data.priority, numbers.Integral):
            raise TypeError("Priority is not Integral")
        if (isinstance(message, FlowModQuery) and
                message.data.command not in
                of.ofp_flow_mod_command_map):
            raise TypeError("Unknown flow_mod command")
        flowmods = []
        if isinstance(message, FlowModQuery):
            flowmods = self._find_flow_mod(message)
        elif isinstance(message, RuleQuery):
            try:
                flowmods = self._find_rule(message)
            except Exception as e:
                log.debug(str(e))
                raise
        #log.debug(str(flowmods))
        code = []
        try:
            for type, ID in flowmods:
                code.append((type, self.show_code(ID)))
        except Exception as e:
            log.debug("%s %s" % (e, flowmods))
        return QueryReply(code=code, qid=message.qid)

    def _get_id_by_query(self, query):
        cur = self.con.cursor()
        queries = query.split(';')
        for q in queries:
            if q.isspace() or q == '':
                continue
            cur.execute(q)
            '''
            #Early exit
            if q == ' SELECT @var':
                res = cur.fetchone()
                if res is not None and res[0] is not None:
                    return res[0]
            '''
        res = cur.fetchone()
        cur.close()
        if res is not None:
            return res[0]

# Save data to a specific table.

    def _save_actions(self, data):
        action_ids = []
        for action in data.actions:
            act_id = self.actions.find(action)
            if act_id is None:
                act_id = self._get_id_by_query(add_actions(action))
                if act_id is not None:
                    self.actions.add(action, act_id)
            action_ids.append(act_id)
        return action_ids

    def _save_code_entries(self, code_entries):
        codeentry_ids = []
        for code_entry in code_entries:
            ce_id = self.code_entries.find(code_entry)
            if ce_id is None:
                ce_id = self._get_id_by_query(add_code_entries(code_entry))
                if ce_id is not None:
                    self.code_entries.add(code_entry, ce_id)
            codeentry_ids.append(ce_id)
        return codeentry_ids

    def _save_action_pattern(self, action_ids):
        actionpat_id = self.action_patterns.find(action_ids)
        if actionpat_id is None and len(action_ids) > 0:
            actionpat_id = self._get_id_by_query(
                QueryCreator.get_actionpat_id_subquery_ids(action_ids) +
                "SELECT @actionpat_ID;")
            self.action_patterns.add(action_ids, actionpat_id)
        return actionpat_id

    def _save_code_pattern(self, codeentry_ids):
        codepat_id = self.code_patterns.find(codeentry_ids)
        if codepat_id is None and len(codeentry_ids) > 0:
            codepat_id = self._get_id_by_query(
                QueryCreator.get_codepat_id_subquery_ids(codeentry_ids) +
                "SELECT @codepat_ID;")
            if codepat_id is not None:
                self.code_patterns.add(codeentry_ids, codepat_id)
        return codepat_id

    def _save_params(self, data):
        params_ID = self.params.find(data)
        if params_ID is None:
            params_ID = self._get_id_by_query(add_flow_mod_params(data))
            if params_ID is not None:
                self.params.add(data, params_ID)
        return params_ID

    def _select_match(self, data):
        q = select_flow_match(data.match, fields="ID", args=None)
        match_ID = self._get_id_by_query(q)
        return match_ID

    def _insert_match(self, data):
        q = insert_flow_match(data.match, args=None)
        q += " SELECT LAST_INSERT_ID(); "
        match_ID = self._get_id_by_query(q)
        return match_ID

    def _save_match(self, data):
        match_ID = self.matches.find(data.match)
        if match_ID is None:
            match_ID = self._select_match(data)
            if match_ID is None:
                match_ID = self._insert_match(data)
            if match_ID is not None:
                self.matches.add(data.match, match_ID)
        return match_ID

    def _save_flow_mod(self, match_ID, params_ID, dpid,
                       actionpat_id, codepat_id):
        query = insert_flow_mods(
            match_ID, params_ID, dpid, actionpat_id, codepat_id)
        query = query.replace('None', 'NULL')
        self._get_id_by_query(query)

    def _save_data(self, message):
        """
        Store FlowMod message to database.
        """
        dpid = message.dpid
        data = message.data
        code_entries = message.code_entries

        action_ids = self._save_actions(data)
        codeentry_ids = self._save_code_entries(code_entries)
        actionpat_id = self._save_action_pattern(action_ids)
        codepat_id = self._save_code_pattern(codeentry_ids)
        params_ID = self._save_params(data)
        match_ID = self._save_match(data)
        self._save_flow_mod(match_ID, params_ID, dpid,
                            actionpat_id, codepat_id)

# Find database ID of data piece by value.

    def _find_action(self, action, update_cache=False):
        act_id = self.actions.find(action)
        if act_id is None:
            act_id = self._get_id_by_query(select_actions(action, fields='ID'))
            if act_id is not None and update_cache:
                self.actions.add(action, act_id)
        return act_id

    def _find_action_pattern(self, actions, update_cache=False):
        action_ids = [self._find_action(a) if isinstance(a, of.ofp_action_base)
                      else a for a in actions]
        if None in action_ids:
            return None
        actionpat_id = self.action_patterns.find(action_ids)
        # Cache miss?
        if actionpat_id is None and len(action_ids) > 0:
            actionpat_id = self._get_id_by_query(
                QueryCreator.find_actionpat_id_subquery_ids(action_ids))
            if actionpat_id is not None and update_cache:
                self.action_patterns.add(action_ids, actionpat_id)
        return actionpat_id

    def _find_match(self, match, update_cache=False):
        match_ID = self.matches.find(match)
        if match_ID is None:
            match_ID = self._get_id_by_query(
                select_flow_match(match, fields='ID', args=None))
            if match_ID is not None and update_cache:
                self.matches.add(match, match_ID)
        return match_ID

    def _find_flow_mod(self, message):
        """
        Select flowmod_ID for last FlowMod with these match, dpid and actions.
        """
        actions = message.data.actions
        match = message.data.match
        dpid = message.dpid
        command = message.data.command
        priority = message.data.priority

        null_result = [(of.ofp_flow_mod_command_map[command], None)]

        actionpat_id = self._find_action_pattern(actions)
        if actionpat_id is None and len(actions) > 0:
            return null_result

        match_ID = self.matches.find(match)
        query = ""
        if match_ID is not None:
            query = "".join([
                         "SELECT max(FlowMods.ID) FROM FlowMods ",
                         "JOIN FlowModParams ON ",
                         "FlowMods.params_ID = FlowModParams.ID AND ",
                         "match_ID <=> %d AND ",
                         "dpid <=> %d AND ",
                         "actionpat_ID <=> %s AND ",
                         "command = %d AND priority = %d",
                         ]) % (
                    match_ID, dpid, actionpat_id, command, priority)
        else:
            tmp = select_flow_match(match, fields='ID', args=None)
            tmp = tmp[(tmp.find('WHERE') + 6):tmp.find('LIMIT')]
            query += "".join([
                          "SELECT max(FlowMods.ID) From FlowMods",
                          " JOIN FlowMatch ON FlowMods.match_ID=FlowMatch.ID"
                          " AND ",
                          tmp,
                          " AND dpid <=> %d AND actionpat_ID <=> %s ",
                          "JOIN FlowModParams ON ",
                          "FlowMods.params_ID = FlowModParams.ID AND ",
                          "command = %d AND priority = %d"]) % (
                        dpid, actionpat_id, command, priority)

        query = query.replace('None', 'NULL')
        cur = self.con.cursor()
        cur.execute(query)
        id = cur.fetchone()
        while cur.nextset() is not None:
            id = cur.fetchone()
        if id is not None and id[0] is not None:
            return [(of.ofp_flow_mod_command_map[command], id[0])]
        return null_result

# Find flow_mods of specific type.

    def _find_adds(self, match_ID, dpid, priority, additionals=None):
        if match_ID is None:
            return []
        if additionals is None:
            additionals = []
        query = "".join(["SELECT FlowMods.ID from FlowMods join FlowModParams",
                         " ON FlowMods.params_ID = FlowModParams.ID AND",
                         " match_ID = %d AND dpid = %d AND",
                         " command = %d AND priority = %d"]) % (
                         match_ID, dpid,
                         of.ofp_flow_mod_command_rev_map["OFPFC_ADD"],
                         priority)
        cur = self.con.cursor()
        if len(additionals) > 0:
            query = query.replace(
                    "FlowMods.ID",
                    "FlowMods.ID, " + ", ".join(additionals))
            cur.execute(query)
            return cur.fetchall()
        cur.execute(query)
        return [id for id, in cur.fetchall()]

    def _find_modifies(self, actionpat_ID=None, dpid=None, priority=None,
                       strict=None, single=False, match_ID=None, match=None,
                       wider=False, additionals=None):
        """
        Select by three first params.
            @param strict -> flow_mod command: True, False,
                                               None ~ (True or False)
            @param single -> True ~ 'max'
                             'max', 'min', 'avg', 'count' accepted
                             False: select all
            @param additional -> return extra fields.
                                 Will return list of tuples.
            @param match_ID -> not None: include in query
                               None: use following params:
            @param match -> if not None, used in query
            @param wider -> True: wider than given
                            False: find match_ID and use it
        """
        if single is True:
            single = 'max'
        if single and single not in ['min', 'max', 'avg', 'count']:
            raise Exception('invalid "single" value')
        if additionals is None:
            additionals = []
        elif not isinstance(additionals, list):
            raise Exception('additionals is not list')
        params_cond = ""
        if strict is not None:
            cmd = "OFPFC_MODIFY_STRICT" if strict else "OFPFC_MODIFY"
            params_cond = "command = %d" % (
                    of.ofp_flow_mod_command_rev_map[cmd])

        else:
            params_cond = "command in (%d, %d)" % (
                of.ofp_flow_mod_command_rev_map["OFPFC_MODIFY"],
                of.ofp_flow_mod_command_rev_map["OFPFC_MODIFY_STRICT"])

        if priority is not None:
            params_cond += " AND priority = %d" % (priority)

        query = ""
        if match_ID is None and match is not None and not wider:
             match_ID = self.matches.find(match)

        if match_ID is None:
            query = "".join(["SELECT FlowMods.ID FROM FlowMods ",
                             "JOIN FlowModParams ON ",
                             "FlowMods.params_ID = FlowModParams.ID AND "
                             "dpid = %d "]) % dpid
            if actionpat_ID is not None:
                query += "AND actionpat_ID <=> %s " % actionpat_ID
            query += "AND " + params_cond
            if match is not None and wider:
                # Hack. Reduce output by selection
                # only matches those are wider than given one.

                # HINT: OF 1.0: subnet mask is in wildcards.
                #       it must be greater or equal.
                match_cond = " (~wildcards & %d = 0) " % ( match.wildcards &
                        ~of.OFPFW_NW_SRC_MASK & ~of.OFPFW_NW_DST_MASK)
                match_cond += ("AND (wildcards & %d >= %d) " * 2) % (
                        of.OFPFW_NW_SRC_MASK,
                        match.wildcards & of.OFPFW_NW_SRC_MASK,
                        of.OFPFW_NW_DST_MASK,
                        match.wildcards & of.OFPFW_NW_DST_MASK)
                # Force to use index.
                # TODO: nw_src, nw_dst lookup is incorrect.
                #       we have to match by mask.
                for f in ["in_port", "dl_src", "dl_dst", "dl_vlan",
                          "dl_vlan_pcp", "dl_type", "nw_tos", "nw_proto",
                          "nw_src", "nw_dst", "tp_src", "tp_dst"]:
                    value = getattr(match, f)
                    if value is not None:
                        # We know that wildcards are wider than ours.
                        # IP prefixes must match.
                        if isinstance(value, IPAddr) and f == "nw_src":
                            match_cond += "".join([
                                "AND (%s <=> NULL ||",
                                " (%s ^ %d) &",
                                " ~((1 << ((wildcards & %d) >> %d))-1) = 0) "
                                ]) % (
                                f, f, ip_to_uint(value),
                                of.OFPFW_NW_SRC_MASK, of.OFPFW_NW_SRC_SHIFT)
                        elif isinstance(value, IPAddr) and f == "nw_dst":
                            match_cond += "".join([
                                "AND (%s <=> NULL ||",
                                " (%s ^ %d) &",
                                " ~((1 << ((wildcards & %d) >> %d))-1) = 0) "
                                ]) % (
                                f, f, ip_to_uint(value),
                                of.OFPFW_NW_DST_MASK, of.OFPFW_NW_DST_SHIFT)
                        elif isinstance(value, EthAddr):
                            match_cond += "AND (%s <=> NULL || %s = %d) " % (
                                f, f, eth_to_int(value))
                        else:
                            match_cond += "AND (%s <=> NULL || %s = %d) " % (
                                f, f, value)
                    else:
                        match_cond += "AND (%s <=> NULL) " % (f)
                match_query = "".join([" JOIN FlowMatch ON",
                                       " FlowMods.match_ID = FlowMatch.ID AND",
                                       match_cond])

                query = query.replace(
                        "FlowMods JOIN FlowModParams ON"
                        " FlowMods.params_ID = FlowModParams.ID",
                        "FlowMods JOIN FlowMatch "
                        "ON FlowMods.match_ID = FlowMatch.ID")
                query = query.replace(
                        "AND command",
                        "".join(["AND ", match_cond, " JOIN FlowModParams ON ",
                                 "FlowMods.params_ID = FlowModParams.ID",
                                 " AND command"]))
                '''
                query += match_query
                '''
            elif match is not None and not wider:
                tmp = select_flow_match(match, fields='ID', args=None)
                tmp = tmp[(tmp.find('WHERE') + 6):tmp.find('LIMIT')]
                query += "".join([" JOIN FlowMatch ON "
                                  "FlowMods.match_ID=FlowMatch.ID",
                                  " AND ", tmp])
        else:
            query = "".join(["SELECT FlowMods.ID FROM FlowMods join",
                             " FlowModParams ON",
                             " FlowMods.params_ID = FlowModParams.ID",
                             " AND match_ID = %d AND dpid = %d "
                             ]) % (match_ID, dpid)
            if actionpat_ID is not None:
                query += " AND actionpat_ID <=> %s " % (actionpat_ID)
            query += " AND " + params_cond

        query = query.replace("FlowMods.ID", "(FlowMods.ID)")
        if single:
            query = query.replace("SELECT (FlowMods.ID)",
                                  "SELECT " + single + "(FlowMods.ID)")

        cur = self.con.cursor()

        def f6(cur, query):
            return cur.execute(query)
        def f7(cur, query):
            return cur.execute(query)
        def f8(cur, query):
            if wider:
                f6(cur, query)
            else:
                f7(cur, query)

        if len(additionals) > 0:
            query = query.replace(
                    "(FlowMods.ID)",
                    "(FlowMods.ID), " + ", ".join(additionals))
            #cur.execute(query)
            f8(cur, query)
            return cur.fetchall()
        #cur.execute(query)
        f8(cur, query)
        return [id for id, in cur.fetchall()]

# Get variuos data pieces for given flowmod_ids.

    def _get_action_patterns(self, flowmod_ids):
        if len(flowmod_ids) == 0:
            return []
        query = "SELECT actionpat_ID FROM (select 1 as num, %d as ID " % (
                    flowmod_ids[0])
        query += "".join(["UNION ALL SELECT %d, %d " % (num, fm)
                          for num, fm in enumerate(flowmod_ids[1:], start=2)])
        query += ") SearchSet NATURAL JOIN FlowMods order by num;"
        cur = self.con.cursor()
        cur.execute(query)
        return [id for id, in cur.fetchall()]

    def _get_matches(self, flowmod_ids):
        if len(flowmod_ids) == 0:
            return []
        query = "SELECT match_ID FROM (select 1 as num, %d as ID " % (
                    flowmod_ids[0])
        query += "".join(["UNION ALL SELECT %d, %d " % (num, fm)
                          for num, fm in enumerate(flowmod_ids[1:], start=2)])
        query += ") SearchSet NATURAL JOIN FlowMods order by num;"
        cur = self.con.cursor()
        cur.execute(query)
        return [id for id, in cur.fetchall()]

    def _get_commands(self, flowmod_ids):
        if len(flowmod_ids) == 0:
            return []
        query = ("SELECT FlowModParams.command FROM" +
                " (select 1 as num, %d as ID ") % (
                    flowmod_ids[0])
        query += "".join(["UNION ALL SELECT %d, %d " % (num, fm)
                          for num, fm in enumerate(flowmod_ids[1:], start=2)])
        query += ") SearchSet NATURAL JOIN FlowMods "
        query += "JOIN FlowModParams on FlowMods.params_ID = FlowModParams.ID "
        query += "ORDER BY num;"
        cur = self.con.cursor()
        cur.execute(query)
        return [id for id, in cur.fetchall()]


    def _get_command(self, flowmod_id):
        query = "".join(["SELECT FlowModParams.command FROM FlowMods JOIN",
                         " FlowModParams ON FlowMods.params_ID =",
                         " FlowModParams.ID and FlowMods.ID=%d"]) % flowmod_id
        cur = self.con.cursor()
        cur.execute(query)
        return cur.fetchall()[0][0]


# Utility to create matches from data in db.

    def _select_match_rev(self, match_ID):
        query = "SELECT * FROM FlowMatch WHERE ID = %d" % match_ID
        cur = self.con.cursor(mdb.cursors.DictCursor)
        cur.execute(query)
        return self._create_match(cur.fetchall()[0])

    def _create_match(self, d):
        m = of.ofp_match()
        for attr in ["wildcards", "in_port", "dl_vlan", "dl_vlan_pcp",
                     "dl_type", "nw_tos", "nw_proto", "tp_src", "tp_dst"]:
            setattr(m, attr, d.get(attr))
        for ip in ["nw_src", "nw_dst"]:
            x = d.get(ip)
            if x is not None:
                setattr(m, ip, uint_to_ip(x))
        for mac in ["dl_src", "dl_dst"]:
            x = d.get(mac)
            if x is not None:
                setattr(m, mac, int_to_eth(x))
        return m

    def _find_rule(self, message):
        """
        Rule can be installed as-is or
        with different actions and then modified to
        the final state.
        In OF 1.2-, MODIFY acts as ADD if table has no matches.
        """
        # Naming: good_* ~ has actions that we want.

        actions = message.data.actions
        match = message.data.match
        dpid = message.dpid
        priority = message.data.priority
        null_result = [("OFPFC_ADD", None)]


        match_ID = self._find_match(match)
        if match_ID is None:
            return null_result
        adds = sorted(self._find_adds(match_ID, dpid, priority,
                                      additionals=["actionpat_ID"]),
                          key=lambda tup: tup[0])
        actionpat_ID = self._find_action_pattern(actions)

        if len(adds) == 0:
            # No flow_mod/add with such header/priority.
            # We should check flow_mod/modify*.
            # HINT: This is changed in OF 1.3+.

            # tuple of tuples: (ID, actionpat_ID, command)
            match_mods = self._find_modifies(
                    None, dpid, priority, strict=None, single=None,
                    match_ID=match_ID,
                    additionals=["actionpat_ID", "command"])

            # No chances to install rule.
            if len(match_mods) == 0:
                return null_result

            # list of tuples
            match_mods = sorted(match_mods, key=lambda tup: tup[0])

            # As-is flow_mod/add
            good_adds = [tup for tup in match_mods if tup[1] == actionpat_ID]

            # We should probably pick the first
            # flow_mod/modify as preferred add.
            # First mod is good -> return.
            if len(good_adds) > 0 and match_mods[0] == good_adds[0]:
                return [(of.ofp_flow_mod_command_map[match_mods[0][2]],
                         match_mods[0][0])]

            # We treat only the first flow_mod/modify as add.
            # Maybe we need more complex heuristic.

            # Now we take the last flow_mod/modify as modify.
            good_mod_ids = self._find_modifies(actionpat_ID, dpid, priority,
                                               strict=False, single='max',
                                               match=match, wider=True)
            good_mods = [(x, actionpat_ID,
                          of.ofp_flow_mod_command_rev_map["OFPFC_MODIFY"])
                         for x in good_mod_ids if x is not None]

            good_strict_mods = [tup for tup in good_adds if tup[2] ==
                    of.ofp_flow_mod_command_rev_map["OFPFC_MODIFY_STRICT"]]
            good_mods.extend(good_strict_mods)

            if len(good_mods) == 0:
                # Return the first modify with good actions.
                if len(good_adds) > 0:
                    return [(of.ofp_flow_mod_command_map[good_adds[0][2]],
                             good_adds[0][0])]
                else:
                    return null_result

            max_mod = max(good_mods, key=lambda tup: tup[0])

            # We will pick the first modify as 'add'
            # and the last modify as 'modify'.
            # First 'add' modify cannot be good here.
            return [(of.ofp_flow_mod_command_map[match_mods[0][2]],
                     match_mods[0][0]),
                    (of.ofp_flow_mod_command_map[max_mod[2]],
                     max_mod[0])]

            '''
            #OLD stuff
            mod_add_ids = self._find_modifies(None, dpid, priority,
                                              strict=None, single=None,
                                              match_ID=match_ID)
            # No chances to install rule.
            if len(mod_add_ids) == 0:
                return null_result

            mod_add_ids = sorted(mod_add_ids)
            mod_add_actionpats = self._get_action_patterns(mod_add_ids)

            # As-is flow_mod/add
            good_adds = [id for id, ap in zip(mod_add_ids, mod_add_actionpats)
                         if ap == actionpat_ID]

            # We should probably pick the first
            # flow_mod/modify as preferred add.
            # First mod is good -> return.
            if mod_add_ids[0] in good_adds:
                return [(of.ofp_flow_mod_command_map[
                    self._get_command(mod_add_ids[0])], mod_add_ids[0])]

            # We treat only the first flow_mod/modify as add.
            # Maybe we need more complex heuristic.

            # Now we take the last flow_mod/modify as modify.
            good_mods = self._find_modifies(actionpat_ID, dpid, priority,
                                               strict=False, single='max',
                                               match=match, wider=True)

            good_add_commands = self._get_commands(good_adds)
            good_strict_mods = [id for id, c in zip(
                good_adds, good_add_commands)
                if c == of.ofp_flow_mod_command_rev_map["OFPFC_MODIFY_STRICT"]]
            good_mods.extend(good_strict_mods)

            if len(good_mods) == 0:
                # Return the first modify with good actions.
                if len(good_adds) > 0:
                    return [(of.ofp_flow_mod_command_map[
                        self._get_command(good_adds[0])], good_adds[0])]
                else:
                    return null_result

            max_mod = max(good_mods)
            command = ("OFPFC_MODIFY_STRICT" if max_mod in good_strict_mods
                       else "OFPFC_MODIFY")

            # We will pick the first modify as 'add'
            # and the last modify as 'modify'.
            # First 'add' modify cannot be good here.
            return [(of.ofp_flow_mod_command_map[
                        self._get_command(mod_add_ids[0])], mod_add_ids[0]),
                    (command, max_mod)]
            '''

        else:
            # We have adds. Do not treat flow_mod/modify as 'add'.
            # As-is flow_mod/add
            good_adds = [tup for tup in adds if tup[1] == actionpat_ID]

            # Last add is good -> return.
            if len(good_adds) > 0 and adds[-1] == good_adds[-1]:
                return [('OFPFC_ADD', adds[-1][0])]
            # Last add is not good -> last can be modified to good.
            # We only need the last good modify.

            good_mod_ids = self._find_modifies(actionpat_ID, dpid,priority,
                                               strict=False, single='max',
                                               match=match, wider=True)
            good_mod_ids = [x for x in good_mod_ids if x is not None]

            good_strict_mod_ids = self._find_modifies(
                    actionpat_ID, dpid, priority, strict=True,
                    single='max', match_ID=match_ID)
            good_strict_mod_ids = [x for x in good_strict_mod_ids
                                   if x is not None]

            # We checked match correctness in _find_modifies.
            good_mod_ids.extend(good_strict_mod_ids)

            if len(good_mod_ids) == 0:
                # Only adds.
                if len(good_adds) > 0:
                    return [('OFPFC_ADD', good_adds[-1][0])]
                else:
                    return null_result

            max_mod = max(good_mod_ids)
            command = ("OFPFC_MODIFY_STRICT"
                       if max_mod in good_strict_mod_ids
                       else "OFPFC_MODIFY")

            # Decide what was later: good add or bad add + modify.
            # Candidate: last add before last good modify.
            try:
                max_add = max([tup[0] for tup in adds if tup[0] < max_mod])
            except:
                return null_result
            #Last good add was later -> return it.
            if len(good_adds) > 0 and good_adds[-1][0] > max_mod:
                return [('OFPFC_ADD', good_adds[-1][0])]
            # Last good add was before good mod -> return ADD + MOD.
            # Probably good_add + good_mod.
            return [('OFPFC_ADD', max_add), (command, max_mod)]

# Backdoor ;-)

    def execute_query(self, query, cursor=None):
        """ Execute given query with specific cursor. """
        if self.con:
            cur = None
            if cursor is None or cursor == self.SIMPLE:
                cur = self.con.cursor()
            elif cursor == self.DICTIONARY:
                cur = self.con.cursor(mdb.cursors.DictCursor)
            if cur is None:
                return None
            cur.execute(query)
            rows = cur.fetchall()
            return rows


