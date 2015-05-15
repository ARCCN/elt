#!/usr/bin/python

from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info

from mininet.topo import Topo
from collections import namedtuple


#our_network = IPAddr('10.0.0.0/24')
server_port = 4
our_network_port = 2
our_network_port_2 = 3
outer_network_port = 1


class ELT_Test(Topo):
    def __init__(self):
        Topo.__init__(self)

        self.addSwitch("s1")
        '''
        self.addHost("outer", ip="10.0.1.1")
        self.addHost("our_1", ip="10.0.0.1")
        self.addHost("our_2", ip="10.0.0.2")
        self.addHost("server", ip="10.0.0.255")
        '''
        self.addSwitch("s2")
        self.addSwitch("s3")
        self.addSwitch("s4")
        self.addSwitch("s5")

        '''
        self.addLink("s1", "outer", outer_network_port)
        self.addLink("s1", "our_1", our_network_port)
        self.addLink("s1", "our_2", our_network_port_2)
        self.addLink("s1", "server", server_port)
        '''
        self.addLink("s1", "s2", outer_network_port)
        self.addLink("s1", "s3", our_network_port)
        self.addLink("s1", "s4", our_network_port_2)
        self.addLink("s1", "s5", server_port)


def emptyNet():

   net = Mininet(topo=ELT_Test(), controller=RemoteController, switch=OVSKernelSwitch, build=False)

   c1 = net.addController('c1', controller=RemoteController, ip="127.0.0.1", port=6640)
   c2 = net.addController('c2', controller=RemoteController, ip="127.0.0.1", port=6641)

   net.build()
   c1.start()
   c2.start()

   for sw in net.switches:
        sw.start([c1,c2])

   net.start()
   net.staticArp()
   CLI( net )
   net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    emptyNet()
