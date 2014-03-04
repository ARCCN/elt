import numbers
import socket
import MySQLdb as mdb

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

    def connect(self):
        try:
            self.con = mdb.connect(self.domain, self.user,
                                   self.password, self.table_name)
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

    def process_message(self, message):
        """
        Save FlowMod data, respond queries.
        """
        if not isinstance(message, Message):
            return None
        if isinstance(message, FlowModMessage):
            try:
                return self.save_data(message)
            except Exception as e:
                log.debug(str(e))
                return e
        elif (isinstance(message, FlowModQuery) or
              isinstance(message, RuleQuery)):
            try:
                return self.reply_query(message)
            except Exception as e:
                log.debug(str(e))
                return e
        return None

    def reply_query(self, message):
        """
        Assert parameter types.
        Return (call_stack, qid).
        """
        if not isinstance(message.data.match, of.ofp_match):
            raise TypeError("Match is not instance of ofp_match")
        for a in message.data.actions:
            #print a
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
            flowmods = self.find_flow_mod(message)
        elif isinstance(message, RuleQuery):
            try:
                flowmods = self.find_rule(message)
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
        if actionpat_id is None:
            actionpat_id = self._get_id_by_query(
                QueryCreator.get_actionpat_id_subquery_ids(action_ids) +
                "SELECT @actionpat_ID;")
            self.action_patterns.add(action_ids, actionpat_id)
        return actionpat_id

    def _save_code_pattern(self, codeentry_ids):
        codepat_id = self.code_patterns.find(codeentry_ids)
        if codepat_id is None:
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

    #@profile
    def save_data(self, message):
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

    def show_code(self, id):
        """
        Return call stack for FlowMod with ID.
        """
        if id is None:
            return 'Not found'
        if self.con:
            query = ("SELECT module, line FROM (CodeEntries INNER JOIN "
                     "CodePatternsToCodeEntries ON CodeEntries.ID = "
                     "CodePatternsToCodeEntries.codeentry_ID) WHERE "
                     "codepat_ID <=> (SELECT codepat_ID FROM FlowMods "
                     "WHERE ID = %s);") % (id)
            cur = self.con.cursor()
            cur.execute(query)
            rows = cur.fetchall()
            while cur.nextset() is not None:
                rows = cur.fetchall()
            return rows

    def find_action(self, action, update_cache=False):
        act_id = self.actions.find(action)
        if act_id is None:
            act_id = self._get_id_by_query(select_actions(action, fields='ID'))
            if act_id is not None and update_cache:
                self.actions.add(action, act_id)
        return act_id

    def find_action_pattern(self, actions, update_cache=False):
        action_ids = [self.find_action(a) if isinstance(a, of.ofp_action_base)
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

    def find_match(self, match, update_cache=False):
        match_ID = self.matches.find(match)
        if match_ID is None:
            match_ID = self._get_id_by_query(
                select_flow_match(match, fields='ID', args=None))
            if match_ID is not None and update_cache:
                self.matches.add(match, match_ID)
        return match_ID


    def find_flow_mod(self, message):
        """
        Select flowmod_ID for last FlowMod with these match, dpid and actions.
        """
        actions = message.data.actions
        match = message.data.match
        dpid = message.dpid
        command = message.data.command
        priority = message.data.priority

        null_result = [(of.ofp_flow_mod_command_map[command], None)]

        actionpat_id = self.find_action_pattern(actions)
        if actionpat_id is None and len(actions) > 0:
            #log.debug('No actionpat_ID')
            return null_result

        match_ID = self.find_match(match)
        if match_ID is None:
            #log.debug('No match_ID')
            return null_result

        query = "".join(["SELECT ID FROM FlowModParams WHERE command=%d ",
                         "AND priority=%d"]) % (
                    command, priority)

        '''
        query = "".join(["SELECT max(ID) FROM FlowMods WHERE ",
                         "dpid <=> %d AND ",
                         "actionpat_ID <=> %s AND "
                         "params_ID in (%s) AND "
                         "match_ID <=> %d"]) % (
                    dpid, actionpat_id, query, match_ID)
        '''
        query = "".join(["SELECT max(ID) FROM FlowMods WHERE ",
                         "match_ID <=> %d AND ",
                         "dpid <=> %d AND ",
                         "actionpat_ID <=> %s AND ",
                         "params_ID in (%s)",
                         ]) % (
                    match_ID, dpid, actionpat_id, query)


        if actions is not None and len(actions) > 0:
            query += " AND actionpat_ID IS NOT NULL"
        query += ";"
        query = query.replace('None', 'NULL')
        cur = self.con.cursor()
        cur.execute(query)
        id = cur.fetchone()
        while cur.nextset() is not None:
            id = cur.fetchone()
        if id is not None and id[0] is not None:
            return [(of.ofp_flow_mod_command_map[command], id[0])]
        #log.debug('No flowmod')
        return null_result

    def find_adds(self, match, dpid, priority):
        match_ID = self.find_match(match)
        if match_ID is None:
            return []

        query = "".join(["SELECT ID FROM FlowModParams WHERE command=%d ",
                         "AND priority=%d"]) % (
                    of.ofp_flow_mod_command_rev_map["OFPFC_ADD"], priority)

        query = "".join(["SELECT ID FROM FlowMods WHERE match_ID=%d ",
                         "AND dpid=%d AND params_ID in (%s)"]) % (
                    match_ID, dpid, query)
        cur = self.con.cursor()
        cur.execute(query)
        return [id for id, in cur.fetchall()]

    def get_action_patterns(self, flowmod_ids):
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

    def find_modifies(self, actionpat_ID, dpid, priority, strict=False):
        cmd = "OFPFC_MODIFY_STRICT" if strict else "OFPFC_MODIFY"
        query = "".join(["SELECT ID FROM FlowModParams WHERE command=%d ",
                         "AND priority=%d"]) % (
                    of.ofp_flow_mod_command_rev_map[cmd], priority)

        query = "".join(["SELECT ID FROM FlowMods WHERE dpid=%d ",
                         "AND actionpat_ID=%d AND params_ID in (%s)"]) % (
                    dpid, actionpat_ID, query)
        cur = self.con.cursor()
        cur.execute(query)
        return [id for id, in cur.fetchall()]

    def get_matches(self, flowmod_ids):
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

    def select_match_rev(self, match_ID):
        query = "SELECT * FROM FlowMatch WHERE ID = %d" % match_ID
        cur = self.con.cursor(mdb.cursors.DictCursor)
        cur.execute(query)
        return self.create_match(cur.fetchall())

    def create_match(self, d):
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

    def find_rule(self, message):
        actions = message.data.actions
        match = message.data.match
        dpid = message.dpid
        priority = message.data.priority

        null_result = [("OFPFC_ADD", None)]
        add_ids = sorted(self.find_adds(match, dpid, priority))#
        if len(add_ids) == 0:
            return null_result
        actionpat_ID = self.find_action_pattern(actions)#
        add_actionpats = self.get_action_patterns(add_ids)#
        good_adds = [id for id, actpat in zip(add_ids, add_actionpats)
                    if actpat == actionpat_ID]
        #Last add is good -> return.
        if add_ids[-1] in good_adds:
            return [('OFPFC_ADD', add_ids[-1])]
        #Last add is not good -> last can be modified to good.
        mod_strict_ids = self.find_modifies(actionpat_ID, dpid, priority, strict=True)#
        mod_ids = self.find_modifies(actionpat_ID, dpid, priority, strict=False)#
        mod_matches = [self.select_match_rev(id)
                       for id in self.get_matches(mod_ids)]#
        mod_strict_matches = [self.select_match_rev(id)
                              for id in self.get_matches(mod_strict_ids)]#
        good_mods = [id for id, m in zip(mod_ids, mod_matches)
                     if m.matches_with_wildcards(match)]
        good_strict_mods = [id for id, m in zip(mod_strict_ids, mod_strict_matches)
                            if m == match]
        good_mods.extend(good_strict_mods)
        if len(good_mods) == 0:
            return null_result
        max_mod = max(good_mods)
        command = ("OFPFC_MODIFY_STRICT" if max_mod in good_strict_mods
                   else "OFPFC_MODIFY")
        #Decide what was later: good add or bad add + modify.
        #Candidate:
        try:
            max_add = max([id for id in add_ids if id < max_mod])
        except:
            return null_result
        #Last good add was later -> return it.
        if len(good_adds) > 0 and good_adds[-1] > max_mod:
            return [('OFPFC_ADD', good_adds[-1])]
        #Last good add was before good mod -> return ADD + MOD.
        #Probably good_add + good_mod.
        return [('OFPFC_ADD', max_add), (command, max_mod)]

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


