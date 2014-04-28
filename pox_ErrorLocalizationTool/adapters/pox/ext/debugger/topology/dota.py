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



        for s in range(1, 9):
            nodes[s] = self.addSwitch('s'+str(s))
            
        #for h in hosts.keys():
        #    nodes[h] = self.addHost(h, **hosts[h]._asdict())        
        '''    
        self.addLink(nodes["outerH"], nodes["s1"])
        self.addLink(nodes["s1"], nodes["s2"])
        self.addLink(nodes["s1"], nodes["s3"])
        self.addLink(nodes["s3"], nodes["s4"])
        self.addLink(nodes["s3"], nodes["s2"])
        self.addLink(nodes["s2"], nodes["innerH"])
        self.addLink(nodes["badH"], nodes["s1"])
        '''
        self.addHost('h1')
        #self.addHost('h2')
        #self.addHost('h7')
        self.addHost('h8')
        #self.addHost('h6')
        #self.addHost('h3')
        
        self.addLink('s1', 's2')
        self.addLink('s1', 's3')
        self.addLink('s1', 's4')
        self.addLink('s2', 's5')
        self.addLink('s2', 's6')
        self.addLink('s2', 's3')
        self.addLink('s3', 's4')
        self.addLink('s3', 's5')
        self.addLink('s3', 's6')
        self.addLink('s3', 's7')
        self.addLink('s4', 's6')
        self.addLink('s4', 's7')
        self.addLink('s5', 's6')
        self.addLink('s5', 's8')
        self.addLink('s6', 's7')
        self.addLink('s6', 's8')
        self.addLink('s7', 's8')

        self.addLink('s1', 'h1')
        #self.addLink('s2', 'h2')
        #self.addLink('s7', 'h7')
        self.addLink('s8', 'h8')
        #self.addLink('s6', 'h6')
        #self.addLink('s3', 'h3')


topos = { 'blocks': ( lambda: Blocks() ) }
        
