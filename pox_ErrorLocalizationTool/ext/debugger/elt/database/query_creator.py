from .database_utility import *


class QueryCreator:
    """
    We put here complex queries.
    """

    def __init__(self):
        pass

    @staticmethod
    def substitute(query, args, arg_list):
        if arg_list is not None:
            arg_list.extend(args)
        else:
            query = query % tuple(args)
        return query.replace('None', 'NULL')

    @staticmethod
    def select_if_null(cond, if_null, if_not_null=None, out_var=None):
        """
        [SET out_var=(] SELECT CASE WHEN cond IS NULL THEN (if_null)
        [ELSE (if_not_null)] END [)]
        """
        query = "SELECT CASE WHEN %s IS NULL THEN (%s)" % (cond, if_null)
        if if_not_null is not None:
            query += " ELSE (%s)" % (if_not_null)
        query += " END"
        if out_var is not None:
            query = " SET %s = (%s)" % (out_var, query)
        return query + ";"

    @staticmethod
    def select_actions_ordered(actions, fields="Actions.ID", arg_list=None):
        """
        Returns a query selecting Actions.ID by given actions,
        order preserved.
        """
        args = []
        query = "SELECT " + fields
        query += " FROM Actions INNER JOIN (SELECT %s AS num, %s AS type, \
                  %s AS port, %s AS value "
        args.extend((1, ) + get_action_params(actions[0]))
        for i in range(1, len(actions)):
            query += " UNION ALL SELECT %s, %s, %s, %s "
            args.extend((i + 1, ) + get_action_params(actions[i]))
        query += " ) SearchSet on Actions.port <=> SearchSet.port and \
                  Actions.type <=> SearchSet.type and Actions.value <=> \
                  SearchSet.value ORDER BY SearchSet.num"
        return QueryCreator.substitute(query, args, arg_list)

    @staticmethod
    def find_actionpat_id_subquery_ids(action_ids,
                                       out_var=None, arg_list=None):
        """
        Returns a query selecting ActionPattern.
        """
        args = []
        # TODO: add function in database_utility with add_complex
        if action_ids is None or len(action_ids) < 1:
            return 'NULL'
        query = ""
        query += "SELECT actionpat_ID"
        if out_var is not None:
            query += " INTO " + out_var
        query += (" FROM ( SELECT " +
                  "GROUP_CONCAT(ID SEPARATOR ',') AS xz FROM (SELECT %s AS ID")
        args.append(action_ids[0])
        for i in range(1, len(action_ids)):
            query += " UNION ALL SELECT %s "
            args.append(action_ids[i])
        query += (" ) SearchSet ) a, ( SELECT actionpat_ID" +
                  ", GROUP_CONCAT(action_ID" +
                  " ORDER BY ID SEPARATOR ',') AS xz FROM " +
                  "ActionPatternsToActions GROUP BY actionpat_ID) b WHERE " +
                  "CONCAT(',', a.xz, ',') LIKE " +
                  "CONCAT(',', b.xz, ',') LIMIT 1")
        return QueryCreator.substitute(query, args, arg_list)

    @staticmethod
    def find_actionpat_id_subquery(actions, out_var=None, arg_list=None):
        """
        Returns a query selecting ActionPattern.
        """
        args = []
        # TODO: add function in database_utility with add_complex
        if actions is None or len(actions) < 1:
            return 'NULL'
        query = "SELECT actionpat_ID "
        if out_var is not None:
            query += 'INTO ' + out_var

        fields = " GROUP_CONCAT(Actions.ID ORDER BY SearchSet.num \
                  SEPARATOR ',' ) AS xz "
        query += " FROM ("
        query += QueryCreator.select_actions_ordered(actions, fields, args)
        query += ") a, ( SELECT actionpat_ID, \
                 GROUP_CONCAT(action_ID ORDER BY ID SEPARATOR ',') AS xz \
                 FROM ActionPatternsToActions GROUP BY actionpat_ID) b \
                 WHERE CONCAT(\',\',a.xz,\',\') LIKE \
                 CONCAT(\',\',b.xz,\',\') LIMIT 1"

        return QueryCreator.substitute(query, args, arg_list)

    @staticmethod
    def get_pat_id_subquery_ids(ids, out_var="@actionpat_ID",
                                pat_field="actionpat_ID",
                                entry_field="action_ID",
                                pair_table="ActionPatternsToActions",
                                pat_table="ActionPatterns", arg_list=None):
        """
        Returns a query selecting <pat_table> or
        inserting <pat_table>, <pair_table>[ID, <pat_field>, <entry_field>].
        Sets <out_var>.

        """
        args = []
        # TODO: add function in database_utility with add_complex
        if ids is None or len(ids) < 1:
            return 'SET %s=NULL;' % (out_var)
        query = "SET @var=NULL;"
        query += ("SELECT " + pat_field + " INTO @var FROM ( SELECT " +
                  "GROUP_CONCAT(ID SEPARATOR ',') AS xz FROM (SELECT %s AS ID")
        args.append(ids[0])
        for i in range(1, len(ids)):
            query += " UNION ALL SELECT %s "
            args.append(ids[i])
        query += (" ) SearchSet ) a, ( SELECT " + pat_field +
                  ", GROUP_CONCAT(" + entry_field +
                  " ORDER BY ID SEPARATOR ',') AS xz FROM " +
                  pair_table + " GROUP BY " + pat_field + ") b WHERE " +
                  "CONCAT(',', a.xz, ',') LIKE " +
                  "CONCAT(',', b.xz, ',') LIMIT 1;")
        query += insert_table(pat_table, ignore=True, id_var="@var")
        query += QueryCreator.select_if_null("@var", "SELECT LAST_INSERT_ID()",
                                             "@var", out_var=out_var)
        # TODO: THIS SHIT IS VERY UNSTABLE!
        # We want to insert only if @var=NULL.
        # This is to prevent inserting otherwise;
        tmp = "SELECT ID FROM %s LIMIT 1" % (pair_table)
        query += QueryCreator.select_if_null("@var", "NULL", tmp, "@var")

        query += (" INSERT IGNORE INTO " + pair_table + " (ID, " +
                  pat_field + ", " + entry_field + ") SELECT @var, " +
                  out_var + ", ID from ( SELECT %s as ID ")
        args.append(ids[0])
        for i in range(1, len(ids)):
            query += " UNION ALL SELECT %s "
            args.append(ids[i])
        query += " ) a;\n"
        return QueryCreator.substitute(query, args, arg_list)

    @staticmethod
    def get_actionpat_id_subquery_ids(action_ids, arg_list=None):
        """
        Returns a query selecting ActionPatterns or
        inserting ActionPatterns,
        ActionPatternsToActions. Sets @actionpat_ID.
        """
        q = QueryCreator.get_pat_id_subquery_ids(
            action_ids, out_var="@actionpat_ID", pat_field="actionpat_ID",
            entry_field="action_ID", pair_table="ActionPatternsToActions",
            pat_table="ActionPatterns", arg_list=arg_list)
        return q

    @staticmethod
    def get_codepat_id_subquery_ids(codeentry_ids, arg_list=None):
        """
        Returns a query selecting CodePatterns or
        inserting CodePatterns,
        CodePatternsToCodeEntries. Sets @codepat_ID.
        """
        q = QueryCreator.get_pat_id_subquery_ids(
            codeentry_ids, out_var="@codepat_ID", pat_field="codepat_ID",
            entry_field="codeentry_ID",
            pair_table="CodePatternsToCodeEntries",
            pat_table="CodePatterns", arg_list=arg_list)
        return q
