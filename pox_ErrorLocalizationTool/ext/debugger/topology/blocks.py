from mininet.topo import Topo
from collections import namedtuple

"""
              

          s4(loopback)----s3      badH (10.0.1.1)
                         /  \    /
                        /    \  /
(10.0.0.2)innerH------s2----- s1-------outerH(10.0.0.1)

"""
class Blocks(Topo):
    def __init__(self):
        Topo.__init__(self)        
        
        switches = ["s1", "s2", "s3", "s4"]
        host_opts = namedtuple('host_opts', 'ip mac')
        hosts = {"innerH":host_opts("10.0.0.2", "00:00:00:00:00:02"), 
                "outerH":host_opts("10.0.0.1", "00:00:00:00:00:01"), 
                "badH":host_opts("10.0.1.1", "00:00:00:00:00:03")}
        nodes = {}



        for s in switches:
            nodes[s] = self.addSwitch(s)
            
        for h in hosts.keys():
            nodes[h] = self.addHost(h, **hosts[h]._asdict())        
            
        self.addLink(nodes["outerH"], nodes["s1"])
        self.addLink(nodes["s1"], nodes["s2"])
        self.addLink(nodes["s1"], nodes["s3"])
        self.addLink(nodes["s3"], nodes["s4"])
        self.addLink(nodes["s3"], nodes["s2"])
        self.addLink(nodes["s2"], nodes["innerH"])
        self.addLink(nodes["badH"], nodes["s1"])
        
topos = { 'blocks': ( lambda: Blocks() ) }
        
