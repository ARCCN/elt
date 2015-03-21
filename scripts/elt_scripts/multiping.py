#!/usr/bin/python

"""
multiping.py: monitor multiple sets of hosts using ping

This demonstrates how one may send a simple shell script to
multiple hosts and monitor their output interactively for a period=
of time.
"""

from mininet.net import Mininet
from mininet.node import Node, RemoteController
from mininet.topolib import TreeTopo
from mininet.topo import Topo, SingleSwitchTopo, LinearTopo
from mininet.log import setLogLevel

from select import poll, POLLIN
import time
from time import sleep
import re
import sys
import getopt
import random


CONTROLLERS = 2
CONTROLLER_COUNT = 2


def chunks(l, n):
    "Divide list l into chunks of size n - thanks Stackoverflow"
    return [l[i: i + n] for i in range(0, len(l), n)]


def startpings(host, targetips):
    "Tell host to repeatedly ping targets"

    targetips = ' '.join(targetips)

    # BL: Not sure why loopback intf isn't up!
    host.cmd('ifconfig lo up')

    # Simple ping loop
    cmd = ('( ping -c1 10.0.0.1 > /dev/null;'
           ' for ip in %s; do ' % targetips +
           '  ping -c1 $ip;'
           ' done;'
           ' echo Q ) &'
           )
    #print cmd
    '''
    print ( '*** Host %s (%s) will be pinging ips: %s' %
            ( host.name, host.IP(), targetips ) )
    '''
    host.cmd(cmd)


def multiping(topo, chunksize, seconds):
    "Ping subsets of size chunksize in net of size netsize"

    # Create network and identify subnets
    net = Mininet(topo=create_topo(topo),
                  # controller=RemoteController,
                  autoStaticArp=False,
                  build=False)
                  # ,autoSetMacs=True)

    if CONTROLLERS > 1:
        controllers = [net.addController("c%d" % i, controller=RemoteController,
                                         ip="127.0.0.1", port=6640+i)
                       for i in range(CONTROLLERS)]
        net.build()
        for sw in net.switches:
            sw.start(random.sample(controllers, CONTROLLER_COUNT))
    else:
        net.start()

    hosts = net.hosts
    #subnets = chunks( hosts, chunksize )
    subnets = [
        hosts[:len(hosts)/2],
        hosts[len(hosts)/2:]
        ]

    outputs = {}
    # Create polling object
    fds = [host.stdout.fileno() for host in hosts]
    poller = poll()
    for fd in fds:
        poller.register(fd, POLLIN)
        outputs[fd] = ""

    # Start pings
    for i, j in [(0, 1), (1, 0)]:
        ips = [host.IP() for host in subnets[j]]
        for host in subnets[i]:
            startpings(host, ips)

    trans = re.compile('([0-9]+) packets transmitted')
    rec = re.compile('([0-9]+) received')
    timems = re.compile('mdev = [0-9]+\.[0-9]+/([0-9]+\.[0-9]+)')
    finish = re.compile('Q')
    finished = 0
    t = []
    r = []
    tim = []
    cnt = 0
    avg_tims = []
    # Monitor output
    endTime = time.time() + seconds
    while time.time() < endTime and finished < len(hosts):
        readable = poller.poll(1000)
        for fd, _mask in readable:
            node = Node.outToNode[fd]
            s = node.monitor().strip()
            outputs[fd] += s
            max_index = 0
            for i in trans.finditer(outputs[fd]):
                t.append(int(i.group(1)))
                if i.end() > max_index:
                    max_index = i.end()
            for i in rec.finditer(outputs[fd]):
                r.append(int(i.group(1)))
                if i.end() > max_index:
                    max_index = i.end()
            for i in timems.finditer(outputs[fd]):
                tim.append(float(i.group(1)))
                if i.end() > max_index:
                    max_index = i.end()
            outputs[fd] = outputs[fd][max_index:]
            cnt += 1
            if cnt % 100 == 0:
                avg_tims.append(avg(tim))
                #print '%06d / %06d, %06f, %06f' % (
                #    safe_sum(r), safe_sum(t), avg(tim), avg(tim[-100:]))
            if len(finish.findall(s)) > 0:
                finished += 1

    avg_tims = avg_tims[len(avg_tims) / 2:]
    max_tim = safe_max(avg_tims)
    print '%06d / %06d, %06f in %f' % (safe_sum(r), safe_sum(t), max_tim,
                                       time.time() - (endTime - seconds))

    # Stop pings
    #for host in hosts:
    #    host.cmd( 'kill %while' )

    net.stop()


def safe_max(seq):
    if len(seq) == 0:
        return 0
    return max(seq)


def safe_sum(seq):
    if len(seq) == 0:
        return 0
    return sum(seq)


def avg(seq):
    if len(seq) == 0:
        return 0
    return sum(seq) / len(seq)


class LineTopo(Topo):
    def __init__(self, k=2, h=2):
        super(LineTopo, self).__init__()
        self.k = k
        self.h = h

        switches = []
        for i in xrange(k):
            switch = self.addSwitch('s%s' % (i+1))
            if len(switches) > 0:
                self.addLink(switch, switches[-1])
            switches.append(switch)

        for i in xrange(h*2):
            host = self.addHost('h%s' % (i+1))
            if len(switches) > 0:
                if i < h:
                    self.addLink(host, switches[0])
                else:
                    self.addLink(host, switches[-1])


def create_topo(type="single"):
    if type.startswith("single"):
        l = type.split(',')
        return SingleSwitchTopo(int(l[1]))
    elif type.startswith("linear"):
        l = type.split(',')
        return LinearTopo(int(l[1]))
    elif type.startswith("tree"):
        l = type.split(',')
        return TreeTopo(int(l[1]), int(l[2]))
    elif type.startswith("line"):
        l = type.split(',')
        return LineTopo(int(l[1]), int(l[2]))


topos = {'line': (lambda(h): LineTopo(5, h))}


def main():
    setLogLevel('info')
    topo = 'single,32'
    args = sys.argv[1:]
    optlist, args = getopt.getopt(args, "", ["topo="])
    for k, v in optlist:
        if k == "--topo":
            topo = v
    multiping(topo, chunksize=4, seconds=1200)


if __name__ == '__main__':
    main()
