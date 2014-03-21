import collections
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import *
import time

class FlowMatch:
    """
    Used to store flow information
    Can store multiple values of each parameter
    Also can store ip network addresses: address/mask
    """
    def __init__(self, params):
        """
        Params must be a dictionary {string: <tuple/list of strings>} 
        or {string: string}
        Analyzed parameters' keys are in self.headers
        """
        self.headers = [('dl_src', EthAddr), 
                        ('dl_dst', EthAddr), 
                        ('dl_vlan', int), 
                        ('dl_vlan_pcp', int), 
                        ('dl_type', int),
                        ('nw_tos', int), 
                        ('nw_proto', int), 
                        ('nw_src', IPAddr), 
                        ('nw_dst', IPAddr),
                        ('tp_src', int),
                        ('tp_dst', int)]

        self.fields = {}
        for name, typ in self.headers:
            setattr(self, name, self.iterate_and_fill(name, typ, params))
        self.create_list()

    def create_list(self): 
        """
        self.fields:
        {"field_name" -> self.field_name}
        """
        for name, typ in self.headers:
            self.fields[name] = (getattr(self, name), typ)

    @classmethod
    def from_row(cls, params):
        """
        Create a match from nesessary fields of row
        """
        match = FlowMatch({})
        for name, typ in match.headers:
            setattr(match, name, [match.convert_to_type(name, typ, params)])
        match.create_list()
        return match

    def convert_to_type(self, field, typ, params):
        if field in params.keys():
            try:
                return typ(params[field])
            except:
                pass

    def iterate_and_fill(self, field, typ, params):
        """
        Iterates params[field], converts to typ and returns as a list
        """
        result = []
        if field in params.keys():
            l = params[field]
            if not isinstance(l, collections.Iterable) or isinstance(l, basestring):
                l = [l]
            for item in l:
                if item is None:
                    result.append(None)
                else:
                    if typ is not IPAddr:
                        result.append(typ(item))
                    else:
                        result.append(parseCIDR(item, False))
        return result

    def iterate_and_str(self, field, l, line_sep='\n', val_sep='\n'):
        s = '%-10s' % (field) + line_sep
        prefix = '\t'
        for item in l:
            s += prefix + str(item) + val_sep
        return s

    def make_condition(self, table):
        """
        Make sql "WHERE" condition from match
        """
        result = ''
        first = True
        for field, typ in self.headers:
            list, type = self.fields[field]
            r = self.iterate_condition(table, field, list, type)
            if r is not None:
                if first:
                    result += '(' + r + ')' + '\n'
                    first = False
                else:
                    result += ' and ' + '(' + r + ')' + '\n'
        return result


    def iterate_condition(self, table, name, l, typ):
        """
        Make condition for single parameter (list of values)
        """
        if len(l) == 0:
            return None
        else:
            s = ''
            nullable = False
            first = True
            field = table + '.' + name
            if typ is IPAddr:
                s += ' '
                for item in l:
                    if item is None:
                        nullable = True
                        continue
                    ip, wc = item

                    if first:
                        first = False
                    else:
                        s += ' \nor '
                    if wc == 0:
                        s += ' ' + field + ' = ' + str(ip.toUnsigned())
                    else:
                        s += ' ' + field + ' between ' + str(ip.toUnsigned()) + \
                        ' and ' + str(ip.toUnsigned() + (1 << wc) - 1)
            else:
                s += ' ' + field + ' in ' + '('
                for item in l:
                    if item is None:
                        nullable = True
                        continue
                    if first:
                        first = False
                    else:
                        s += ', '
                    if typ is EthAddr:
                        s += str(item.toInt())
                    else:
                        s += str(item)
                s += ')'
                if first: s = ''
            if nullable:
                if not first:
                    s += ' \nor ' 
                s += field + ' is NULL '
            return s

    

    def __str__(self):
        result = ''
        for field, typ in self.headers:
            list, type = self.fields[field]
            result += self.iterate_and_str(field, list, line_sep='\n', val_sep='\n')
        return result

    def toShortString(self):
        result = ''
        for field, typ in self.headers:
            list, type = self.fields[field]
            result += self.iterate_and_str(field, list, line_sep='\t', val_sep='\n')
        return result


class HistoryMatch:
    """
    Class to store information about dpid/port/time of PacketIn event
    """
    def __init__(self, params):
        self.points = []
        if "point" in params.keys():
            l = params["point"]
            if not isinstance(l, collections.Iterable) or len(l) == 0 \
                or not isinstance(l[0], collections.Iterable):
                l = [l]
            for item in l:
                dpid, port = item
                self.points.append((int(dpid), int(port)))
        self.times = []
        if "time" in params.keys():
            l = params["time"]
            if not isinstance(l, collections.Iterable) or len(l) == 0 \
                    or not isinstance(l[0], collections.Iterable) \
                    or isinstance(l[0], basestring):
                l = [l]
            for item in l:
                start, finish = item
                self.times.append((time.strptime(start, "%Y-%m-%d %H:%M:%S"),
                    time.strptime(finish, "%Y-%m-%d %H:%M:%S")))

    def make_condition(self, table):
        """
        Make sql condition for the time and points
        """
        result = ' '
        first = True
        point_entry = '('
        for point in self.points:
            dpid, port = point
            s = ''
            if dpid != 0:
                s += table + '.' + 'dpid' + ' = ' + str(dpid)
                if port != 0:
                    s += ' and ' + table + '.' + 'in_port' + ' = ' + str(port)
            elif port != 0:
                s += table + '.' + 'in_port' + ' = ' + str(port)
            if s == '': continue
            if first:
                first = False
            else:
                point_entry += ' \nor '
            point_entry += '(' + s + ')'
        point_entry += ')'
        if first: point_entry = ''

        first = True
        time_entry = '('
        for t in self.times:
            start, finish = t
            s = ''
            s += table + '.' + 'time' + ' between \'' + \
                    time.strftime("%Y-%m-%d %H:%M:%S", start)
            s += '\' and \'' + time.strftime("%Y-%m-%d %H:%M:%S", finish) + '\''
            if first:
                first = False
            else:
                time_entry += ' \nor '
            time_entry += '(' + s + ')'
        time_entry += ')'
        if first: time_entry = ''
        
        if point_entry != '':
            result += ' ' + point_entry + '\n'
            if time_entry != '':
                result += ' and ' + time_entry + '\n'
        elif time_entry != '':
            result += ' ' + time_entry + '\n'

        return result

    def __str__(self):
        result = ''
        result += 'points\n'
        prefix = '    '
        for point in self.points:
            result += prefix + str(point[0]) + ':' + str(point[1]) + '\n'
        result += 'times\n'
        for t in self.times:
            result += prefix + time.strftime("%Y-%m-%d %H:%M:%S", t[0]) + \
                    prefix + time.strftime("%Y-%m-%d %H:%M:%S", t[1]) + '\n'
        return result

  
