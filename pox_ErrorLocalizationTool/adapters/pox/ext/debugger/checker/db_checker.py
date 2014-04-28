import exceptions
import collections
from database import Database
import pox.openflow.libopenflow_01 as of
from pox.lib.addresses import *
import time
import networkx as nx
from naive_logger import log
from matches import FlowMatch, HistoryMatch
from xml_report import *

#What shall DbChecker return from SELECT
NOTHING = 0
COUNT = 1
FULL = 2
RETURN = 3

class DBChecker:
    """
    Class for creating queries to database
    """
    def __init__(self):
        self.db = Database()
        self.xml_report = XmlReport('xml_report.xml')
        self.trace_params = {}

    def execute(self, query, output = FULL, cursor=None):
        """
        Execute given query and output result
        """
        try:
            rows = self.db.execute_query(query, cursor)
            if rows is not None:
                if output == FULL:
                    if cursor == self.db.SIMPLE or cursor == None:
                        for row in rows:
                            s = ""
                            for item in row:
                                s = s + str(item) + "\t"
                            print s
                    else:
                        for row in rows:
                            s = ""
                            for name, item in row.items():
                                s = s + str(name) + '='+str(item) + '\t'
                            print s
                    print len(rows)

                elif output == COUNT:
                    print len(rows)
                elif output == RETURN:
                    return rows
            else:
                print "Success"
        except Exception as e:
            print e

    def finish(self):
        self.db.disconnect()

    def choose_by_params(self, **params):
        """
        process user input and make query to database
        """
        match = FlowMatch(params)
        time = HistoryMatch(params)
        query = self._make_query(match, time)
        if 'cursor' in params:
            self.execute(query, cursor=params['cursor'])
        else:
            self.execute(query)

    def _extract_trace_params(self, params):
        result = {}
        if 'check_point' in params:
            result['check_point'] = int(params['check_point'])
        else:
            result['check_point'] = None
        
        if 'print_flow' in params:
            result['print_flow'] = bool(params['print_flow'])
        else:
            result['print_flow'] = True

        if 'draw' in params:
            result['draw'] = bool(params['draw'])
        else:
            result['draw'] = False

        if 'check_full' in params:
            result['check_full'] = bool(params['check_full'])
        else:
            result['check_full'] = False

        if 'write_ports' in params:
            result['write_ports'] = bool(params['write_ports'])
        else:
            result['write_ports'] = True

        return result

    def trace_path(self, **params):
        """
        Check whether subflow goes through check_point
        1. Create match from params
        2. Ask DB for matching PacketIns
        3. Draw full graph and each subflow graph
        4. Check whether subgraph is checkable with our algorithm
        5. If checkable, trace path of subflow to check_point
        6. Output dropped packets to log
        """

        self.xml_report.clear()

        #Flow header fields
        match = FlowMatch(params)
        #time and point(?)
        time = HistoryMatch(params)
        query = self._make_query(match, time)
        rows = self.execute(query, cursor = Database.DICTIONARY, output = RETURN)

        self.trace_params = self._extract_trace_params(params)
        
        full_graph = self._graph_from_routes(rows)

        #separate packets by headers
        flow_routes = {}
        for row in rows:
            if row["ID"] in flow_routes:
                flow_routes[row["ID"]].append(row)
            else:
                flow_routes[row["ID"]] = [row]

        
        #analyze each flow separately
        for ID, routes in flow_routes.items():
            self._check_flow(routes, full_graph, ID, \
                    check_point=self.trace_params['check_point'], 
                    draw=self.trace_params['draw'], 
                    print_flow=self.trace_params['print_flow'])

        if self.trace_params['check_full']:
            self._check_flow(rows, draw=True)
        else:
            self._check_flow(rows, full_graph, check_point=self.trace_params['check_point'],\
                    draw=True, print_flow=False)
        print '%d rows processed' % (len(rows))
        log.flush()
        self.xml_report.flush()


    def _graph_from_routes(self, routes, single_inout=False):
        #Count packets on each link
        paths = {}
        for row in routes:
            t = (row["src_dpid"], row["src_port"], \
                row["dpid"], row["in_port"])
            if t in paths:
                paths[t] += 1
            else:
                paths[t] = 1

        g = self._create_graph(paths, single_inout, self.trace_params['write_ports'])
        return g

    def _check_flow(self, routes, full_graph = None, ID=None, check_point=None, \
            draw=True, print_flow=True):
        g = self._graph_from_routes(routes)
                
        functions = [(self._is_tree_checkable, self._tree_check), \
                     (self._is_separating_checkable, self._separating_check), \
                     (self._is_single_entranced, self._single_entranced_check)]


        is_checkable, check = functions[2]
        #try to check tree
        #TODO: working algorithm
        if check_point is not None:
            log.info('\n\n' + str(ID))
            log.print_store(str(ID))
            self.xml_flow_report = self.xml_report.new_flow(ID)
            if len(routes) > 0:
                match = FlowMatch.from_row(routes[0])
                if print_flow:
                    match_str =  match.toShortString()
                    log.info('\n' + match_str)
                    log.print_store(match_str)
                self.xml_flow_report.set_match(match)
            #Check whether our graph is checkable with our algorithm
            g_check = self._graph_from_routes(routes, single_inout=True)
            if is_checkable(g_check):
                if not check(g, full_graph, check_point):
                    log.print_flush()
                    self.xml_report.add_flow('error', self.xml_flow_report)
                else:
                    log.print_clear()
                    self.xml_report.add_flow('correct', self.xml_flow_report)
            else:
                log.info("Graph is not checkable with current algorithm")
                log.print_store("Graph is not checkable with current algorithm")
                log.print_flush()
                self.xml_report.add_flow('uncheckable', self.xml_flow_report)
                
        if draw:
            if ID is not None:
                self._draw_graph(g, str(ID))
            else:
                self._draw_graph(g, '')

    def _is_single_entranced(self, graph, inner_cycles=None, paths=None):
        """
        We dont want a cycle with two entrances.
        """
        if inner_cycles is None:
            inner_cycles = []
        if paths is None:
            paths = []
        cycles = nx.simple_cycles(graph)
        for cycle in cycles:
            if not 'Input' in cycle:
                points = 0
                for point in cycle[:-1]:
                    for pred in graph.predecessors(point):
                        if pred not in cycle:
                            inner_cycles.append((cycle, point))
                            points += 1
                            break
                if points > 1:
                    log.debug('Cycle with %d entrances: %s' % (points, cycle))
                    self.xml_flow_report.add_comment('Cycle with %d entrances: %s' \
                            % (points, cycle))
                    return False
            else:
                paths.append(cycle)
        return True



    def _is_separating_checkable(self, graph):
        """
        We dont want a cycle with two entrances.
        """
        inner_cycles = []
        paths = []
        if not self._is_single_entranced(graph, inner_cycles, paths):
            return False

        """
        We also dont want a path using only the entrance of a cycle
        meeting another path using part of this cycle.
        """
        for cycle, entrance in inner_cycles:
            using_entrance = set()
            using_part = set()
            #Finding the vertex after entrance in cycle
            for i in range(len(cycle)-1):
                if cycle[i] == entrance:
                    entr_succ = cycle[i+1]
                    break
            for path in paths:
                for i in range(len(path)):
                    if path[i] == entrance:
                        if path[(i+1) % len(path)] == entr_succ:
                            #We are using part of cycle
                            i = (i+2) % len(path);
                            while path[i] != 'Input':
                                using_part.add(path[i])
                                i = (i+1) % len(path)
                            break
                        else:
                            #We are using only the entrance
                            i = (i+1) % len(path)
                            while path[i] != 'Input':
                                using_entrance.add(path[i])
                                i = (i+1) % len(path)

            if len(using_part & using_entrance) > 0:
                log.debug("Path using entrance meets path using part of cycle")
                self.xml_flow_report.add_comment("Path using entrance \
                        meets path using part of cycle")

                return False
        return True

    def _is_tree_checkable(self, graph):
        """
        We don't want non-directed cycles
        """
        if len(nx.cycle_basis(nx.Graph(graph))) > 0:
            return False
        return True

    def _create_simple_paths(self, g, full_graph, check_point):
        """
        Return a list of all routes from entrances to check_point.
        """
        error = False
        list_routes = []
        #Create a path from each start node to check_point
        for start in [node_id for node_id in g.nodes() \
            if isinstance(node_id, basestring) and 'Input' in node_id]:
            count = 0
            paths = []
            try:
                #Find a way to check in our subgraph
                paths = nx.all_simple_paths(g, source=start, target=check_point)
            except Exception as e:
                log.debug(str(e))
                try:
                    #Try to find a path in full graph
                    #TODO: maybe we need only one route
                    #not to get an error below
                    paths = []
                    for succ in g.successors(start):
                        for path in nx.all_simple_paths(full_graph, \
                                source=succ, target=check_point):
                            paths.append(path)
                    
                    for p in paths:
                        #We are the start point on each route.
                        p.insert(0, start)
                        #Put the right weights into our routes.
                        for i in range(2, len(p)):
                            if not g.has_edge(p[i-1], p[i]):
                                g.add_edge(p[i-1], p[i], weight=0, label=0, len=2, \
                                           taillabel='', headlabel='')

                except Exception as e:
                        log.debug(str(e))
                
            #Create a list of all routes
            first_hops = {}
            for path in paths:
                log.info('path : %s' % (str(path)))
                if path[1] not in first_hops:
                    first_hops[path[1]] = 0
                first_hops[path[1]] += g[start][path[1]]['weight']
                list_routes.append(path)
                count += 1

            for dpid, packets in first_hops.items():
                log.info('Packets from source to %d: %d' % (dpid, packets))
                self.xml_flow_report.add_comment('Packets from source to %d: %d' % (dpid, packets))

            #We dont want no paths
            if count == 0:
                error = True
                log.info('No path from %s to %s' % (start, str(check_point)))
                log.print_store('No path from %s to %s' % (start, str(check_point)))
                self.xml_flow_report.add_comment('No path from %s to %s' % (start, str(check_point)))
            elif count > 1:
                log.info('Found %d routes from %s to %s' % \
                        (count, start, str(check_point)))
        if error:
            return None
        return list_routes

    def _single_entranced_check(self, g, full_graph, check_point):

        def decrease_cycles(graph, check_point):
            """
            Decrease every cycle by minimal weight of edge
            """
            for cycle in nx.simple_cycles(graph):   
                if check_point not in cycle:
                    min_weight = graph[cycle[0]][cycle[1]]['weight']
                    for i in range(1, len(cycle)-1):
                        w = graph[cycle[i]][cycle[i+1]]['weight']
                        if w < min_weight:
                            min_weight = w
                    for i in range(0, len(cycle)-1):
                        graph[cycle[i]][cycle[i+1]]['weight'] -= min_weight

        list_routes = self._create_simple_paths(g, full_graph, check_point)
        if list_routes is None:
            return False

        g_processed = g
        decrease_cycles(g, check_point)

        return self._check_simple_paths(g, list_routes)



    def _separating_check(self, g, full_graph, check_point):
        """
        Check flow tree using our algorithm
        """
        list_routes = self._create_simple_paths(g, full_graph, check_point)
        if list_routes is None:
            return False
    
        #Analyze each route from check to start
        return self._check_simple_paths(g, list_routes)

    def _check_simple_paths(self, g, list_routes):
        class Vertex:
            def __init__(self):
                self.enter = {}
                self.exit = {}

            def __str__(self):
                s = 'enter: %s\nexit: %s\n' % (str(self.enter), str(self.exit))
                return s

        result = True
        vertices = {}
        for route in list_routes:
            for i in range(1, len(route)-1):
                #TODO: Probably going on edges instead of vertices
                #      can be twice more efficient
                if route[i] in vertices:
                    vertex = vertices[route[i]]
                else:
                    vertex = Vertex()

                if route[i-1] not in vertex.enter:
                    vertex.enter[route[i-1]] = g[route[i-1]][route[i]]['weight']
                if route[i+1] not in vertex.exit:
                    vertex.exit[route[i+1]] = g[route[i]][route[i+1]]['weight']

                vertices[route[i]] = vertex

        for name, vertex in vertices.iteritems():
            log.debug('name: %s inside: \n %s' % (str(name), str(vertex)))
            enter = exit = 0
            for target_name, val in vertex.enter.iteritems():
                enter += val
            for target_name, val in vertex.exit.iteritems():
                exit += val

            if enter > exit:
                log.info('Lost %d packets in %s' % (enter - exit, str(name)))
                log.print_store('Lost %d packets in %s' % (enter - exit, str(name)))
                self.xml_flow_report.add_comment('Lost %d packets in %s' % (enter - exit, str(name)))

                result = False
            elif enter < exit:
                log.info('Error in %s: in = %d, out = %d' \
                        % (str(name), enter, exit))
                log.print_store('Error in %s: in = %d, out = %d' \
                        % (str(name), enter, exit))
                self.xml_flow_report.add_comment('Error in %s: in = %d, out = %d' \
                        % (str(name), enter, exit))

                result = False
        return result

    def _tree_check(self, g, full_graph, check_point):
        """
        Check flow tree using our algorithm
        """
        routes = {}
        list_routes = []
        error = False
        #Create a path from each start node to check_point
        for start in [node_id for node_id in g.nodes() \
            if isinstance(node_id, basestring) and 'Input' in node_id]:
            #routes[start] = []
            count = 0
            paths = []
            try:
                #Find a way to check in our subgraph
                paths = nx.all_simple_paths(g, source=start, target=check_point)
            except Exception as e:
                log.debug(str(e))
                try:
                    #Try to find a path in full graph
                    #TODO: maybe we need only one route
                    #not to get an error below
                    paths = []
                    for succ in g.successors(start):
                        paths.extend(nx.all_simple_paths(full_graph, \
                                source=succ, target=check_point))
                    #We are the start point on each route
                    for p in paths:
                        p.insert(0, start)
                except Exception as e:
                        log.debug(str(e))
                
            #Create a list of all routes
            first_hops = []
            hop_in = 0
            for path in paths:
                log.info('path : %s' % (str(path)))
                if path[1] not in first_hops:
                    first_hops.append(path[1])
                    hop_in += g[start][path[1]]['weight']
                path.reverse()
                #routes[start].append(path)
                list_routes.append(path)
                count += 1
            log.info('Packets from this source: %d' % (hop_in))

            #We dont want different paths or no paths
            if count == 0:
                error = True
                log.info('No path from %s to %s' % (start, str(check_point)))
            elif count > 1:
                error = True
                log.info('Found %d routes from %s to %s' % \
                        (count, start, str(check_point)))
        if error:
            return False

    
        #Analyze each route from check to start
        return self._traverse(g, list_routes)

    def _traverse(self, g, list_routes):
        """
        Analyze single step on every route from check to start.
        Then call recursively.
        """
        success = True
        next_hops = {}
        if len(list_routes) == 0 or len(list_routes[0]) == 0:
            return success
        current = list_routes[0][0]
        for route in list_routes:
            if len(route) <= 2:
                log.debug("Finish on %s" % (str(route[0])))
            else:
                if route[1] not in next_hops:
                    next_hops[route[1]] = []
                if route[2] not in next_hops[route[1]]:
                    next_hops[route[1]].append(route[2])

        log.debug("Next hops: %s" % (str(next_hops)))
        for next_hop in next_hops.keys():
            in_next = 0
            traverse = True
            next_routes = []
            for route in [route for route in list_routes \
                    if len(route) > 2 and route[1] == next_hop]:
                next_routes.append(route[1:]) 

            for next_next in next_hops[next_hop]:
                try:
                    tmp = g[next_next][next_hop]['weight']
                    log.debug("%s -> %s %d" % (str(next_next), str(next_hop), tmp))
                    in_next += tmp
                except:
                    log.debug("%s -> %s No route" % (str(next_next), str(next_hop)))
            try:
                out_next = g[next_hop][current]['weight']
                log.debug("%s -> %s %d" % (str(next_hop), str(current), out_next))
            except:
                log.debug('%s -> %s No route' % (str(next_hop), str(current)))
                out_next = 0
            
            if out_next < in_next:
                log.info('Lost %d packets in %s' % (in_next-out_next, str(next_hop)))
                success = False
            elif out_next > in_next:
                log.info('Error in %s : in - %d, out - %d ' % \
                        (str(next_hop), in_next, out_next))
                success = False
            if traverse:
                log.debug('traverse with len %d' % (len(next_routes)))
                success &= self.traverse(g, next_routes)

        return success
    
    def _create_graph(self, paths, single_inout=False, write_ports=True):

        g = nx.DiGraph()

        inputs = 0
        for link, num in paths.iteritems():
            l = link[0]
            if link[0] is not None:
                if link[0] not in g.nodes():
                    g.add_node(link[0])
            else:
                if not single_inout:
                    l = "Input" + str(inputs)
                    g.add_node(l, fillcolor='green', style='filled')
                    inputs += 1
                elif 'Input' not in g.nodes():
                        l = "Input"
                        g.add_node(l, fillcolor='green', style='filled')
            if link[2] not in g.nodes():
                g.add_node(link[2])

            if write_ports:
                g.add_edge(l, link[2], weight=num, label=num, src_port=link[1], \
                    taillabel=link[1], in_port=link[3], headlabel=link[3], len=3)
            else:
                g.add_edge(l, link[2], weight=num, label=num, src_port=link[1], \
                    in_port=link[3], len=3)

        if single_inout:
            for node_id in g.nodes():
                if node_id == 'Input':
                    continue
                inp = 0
                out = 0
                for target in g.successors(node_id):
                    out += g[node_id][target]['weight']
                for target in g.predecessors(node_id):
                    inp += g[target][node_id]['weight']
                if inp > out:
                    g.node[node_id]['fillcolor'] = 'blue'
                    g.node[node_id]['style'] = 'filled'
                    g.add_edge(node_id, 'Input', weight=inp-out, label=inp-out, len=2)

        return g
            
    def _draw_graph(self, g, ID=''):
        if ID is None:
            ID = ''
        """
        pos = nx.spring_layout(g)
        center_labels=dict([((u,v,),d['weight'])\
            for u,v,d in g.edges(data=True)])
        start_labels=dict([((u,v,),d['taillabel'])\
            for u,v,d in g.edges(data=True)])
        end_labels=dict([((u,v,),d['headlabel'])\
            for u,v,d in g.edges(data=True)])
        """

        for node_id in g.nodes():
            inp = 0
            out = 0
            for target in g.successors(node_id):
                out += g[node_id][target]['weight']
            for target in g.predecessors(node_id):
                inp += g[target][node_id]['weight']
            if inp > out:
                g.node[node_id]['fillcolor'] = 'blue'
                g.node[node_id]['style'] = 'filled'

        for v1, v2 in g.edges():
            g[v1][v2]['label'] = g[v1][v2]['weight']
            if g[v1][v2]['weight'] == 0:
                g[v1][v2]['style'] = 'dotted'
        """
        nx.draw(g, pos)
        nx.draw_networkx_edges(g, pos, arrows=True)
        nx.draw_networkx_edge_labels(g,pos,edge_labels=center_labels)
        nx.draw_networkx_edge_labels(g,pos,edge_labels=end_labels, label_pos=0.1)
        nx.draw_networkx_edge_labels(g, pos, label_pos=0.9, edge_labels=start_labels)
        """
        nx.write_dot(g, 'graphs/graph' + ID + '.dot')

    def _make_query(self, match, time = None):
        """
        Construct a sql-query from given flow properties
        """
        query = ''
        query += 'Select * from FlowHistory left join FlowMatch '
        query += 'on (FlowHistory.ID = FlowMatch.ID)'
        cond = match.make_condition('FlowMatch')
        t = ''
        if time is not None:
            t = time.make_condition('FlowHistory')
        if cond != '' and not cond.isspace():
            query += ' where\n' + cond
            if t != '' and not t.isspace():
                query += 'and\n' + t
        elif t != '' and not t.isspace():
            query += ' where\n' + t
        print query
        return query


