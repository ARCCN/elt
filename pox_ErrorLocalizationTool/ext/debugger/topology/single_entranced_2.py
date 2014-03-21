from mininet.topo import Topo
from collections import namedtuple


class SingleEntranced(Topo):
    def __init__(self):
        Topo.__init__(self)        
        
        switches = ["s1", "s2", "s3", "s4"]
        host_opts = namedtuple('host_opts', 'ip mac')
        hosts = {
                "h01":host_opts("10.0.0.1", "00:00:00:00:00:01"),
                "h02":host_opts("10.0.0.2", "00:00:00:00:00:02"),
                #"h03":host_opts("10.0.0.3", "00:00:00:00:00:03"),

                "h11":host_opts("10.0.1.1", "00:00:00:00:00:04"),
                "h12":host_opts("10.0.1.2", "00:00:00:00:00:05")
                #"h13":host_opts("10.0.1.3", "00:00:00:00:00:06")
                }
        adjacency = [
                ("s1", "s2"),
                ("s1", "s3"),
                ("s4", "s2"),     
                ("s4", "s3"),
                ("s2", "s3"),
               
                ("s1", "h01"),
                ("s1", "h02"),
                #("s1", "h03"),
                ("s4", "h11"),
                ("s4", "h12")
                #("s4", "h13")
                ]
                
        nodes = {}

        for s in switches:
            self.addSwitch(s)
            
        for h in hosts.keys():
            self.addHost(h, **hosts[h]._asdict())        
            
        for name1, name2 in adjacency:    
            self.addLink(name1, name2)


topos = { 'single_entranced': ( lambda: SingleEntranced() ) }
        
