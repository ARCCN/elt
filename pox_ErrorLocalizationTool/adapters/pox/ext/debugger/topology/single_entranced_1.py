from mininet.topo import Topo
from collections import namedtuple


class SingleEntranced(Topo):
    def __init__(self):
        Topo.__init__(self)        
        
        switches = ["s10", "s11", "s21", "s22", "s23", "s31", "s32", "s33",\
                "s4", "s51", "s52", "s53", "s54"]
        host_opts = namedtuple('host_opts', 'ip mac')
        hosts = {"h10":host_opts("10.0.0.1", "00:00:00:00:00:01"),
                "h52":host_opts("10.0.1.1", "00:00:00:00:00:02"),
                "h53":host_opts("10.0.1.2", "00:00:00:00:00:03"), 
                "h54":host_opts("10.0.1.3", "00:00:00:00:00:04")}
        adjacency = [
                ("s10", "s11", 11, 10),
                ("s11", "s21", 21, 11),
                ("s21", "s22", 22, 21),     
                ("s22", "s23", 23, 22),
                ("s23", "s10", 10, 23),
                ("s21", "s23", 23, 21),
                ("s11", "s31", 31, 11),
                ("s31", "s32", 32, 31),
                ("s32", "s33", 33, 32),
                ("s33", "s10", 10, 33),
                ("s31", "s33", 33, 31),

                ("s21", "s51", 51, 21),
                ("s11", "s51", 51, 11),
                ("s31", "s51", 51, 31),

                ("s21", "s4", 4, 21),
                ("s22", "s4", 4, 22),
                ("s23", "s4", 4, 23),
                ("s31", "s4", 4, 31),
                ("s32", "s4", 4, 32),  
                ("s33", "s4", 4, 33),
                ("s10", "s4", 4, 10),
                ("s4", "s51", 51, 4),
                
                ("s51", "s52", 52, 51),
                ("s52", "s53", 53, 52),
                ("s53", "s54", 54, 53), 
                ("s54", "s51", 51, 54),
                ("s54", "s52", 52, 54),

                ("s10", "h10", 10, None),
                ("s52", "h52", 52, None),
                ("s53", "h53", 53, None),
                ("s54", "h54", 54, None)
                ]
                
        nodes = {}

        for s in switches:
            self.addSwitch(s)
            
        for h in hosts.keys():
            self.addHost(h, **hosts[h]._asdict())        
            

        for name1, name2, port1, port2 in adjacency:    
            self.addLink(name1, name2, port1, port2)


        print self.port("s10", "s11")


topos = { 'single_entranced': ( lambda: SingleEntranced() ) }
        
