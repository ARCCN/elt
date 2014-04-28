from mininet.topo import Topo
from collections import namedtuple

"""
    ___________
   |__|__|__|__|
   |__|__|__|__|
   |__|__|__|__|
   |__|__|__|__|

"""
class Acyclic(Topo):
    def __init__(self):
        Topo.__init__(self)        
        
        for i in range(1, 6):
            for j in range(1, 6):
                self.addSwitch("s%d%d" % (i, j))
                self.addHost("h%d%d" % (i, j))
                self.addLink("s%d%d" % (i, j), "h%d%d" % (i, j))


        for i in range(1, 6):
            for j in range(1, 6):
                if i != 5:
                    self.addLink("s%d%d" % (i, j), "s%d%d" % (i+1, j))
                if j != 5:
                    self.addLink("s%d%d" % (i, j), "s%d%d" % (i, j+1))
            

topos = { 'acyclic': ( lambda: Acyclic() ) }
        
