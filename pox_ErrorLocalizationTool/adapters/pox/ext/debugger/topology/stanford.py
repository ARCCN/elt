from mininet.topo import Topo
from collections import namedtuple


class Stanford(Topo):
    def __init__(self):
        Topo.__init__(self)        
        
        switches = ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8", "s9"]
        host_opts = namedtuple('host_opts', 'ip mac')
        hosts = {
                "h01":host_opts("10.0.0.1", "00:00:00:00:00:01"),
                #"h02":host_opts("10.0.0.2", "00:00:00:00:00:02"),
                #"h03":host_opts("10.0.0.3", "00:00:00:00:00:03"),

                "h11":host_opts("10.0.1.1", "00:00:00:00:00:04"),
                #"h12":host_opts("10.0.1.2", "00:00:00:00:00:05"),

                "h21":host_opts("10.0.2.1", "00:00:00:00:00:06"),
                #"h22":host_opts("10.0.2.2", "00:00:00:00:00:07"),

                "h31":host_opts("10.0.3.1", "00:00:00:00:00:08"),
                #"h32":host_opts("10.0.3.2", "00:00:00:00:00:09")
                #"h13":host_opts("10.0.1.3", "00:00:00:00:00:06")
                }
        adjacency = [
                ("s1", "s2"),
                ("s2", "s3"),
                ("s1", "s4"),     
                ("s1", "s5"),
                ("s5", "s6"),
                ("s4", "s6"),
                ("s4", "s7"),
                ("s6", "s7"),
                ("s7", "s8"),
                ("s7", "s9"),
               
                ("s2", "h01"),
                #("s2", "h02"),
                
                ("s4", "h11"),
                #("s4", "h12"),

                ("s6", "h21"),
                #("s6", "h22"),

                ("s7", "h31"),
                #("s7", "h32")
                ]
                
        nodes = {}

        for s in switches:
            self.addSwitch(s)
            
        for h in hosts.keys():
            self.addHost(h, **hosts[h]._asdict())        
            
        for name1, name2 in adjacency:    
            self.addLink(name1, name2)


topos = { 'stanford': ( lambda: Stanford() ) }
        
