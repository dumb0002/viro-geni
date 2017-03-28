#!/usr/bin/python

import sys
import re
import time
import itertools as it

from mininet.net import Mininet
from mininet.node import OVSKernelSwitch
from mininet.cli import CLI
from mininet.log import setLogLevel

from pox import POX
from viro_host import ViroHost
import util


def loadTopology(ifname):
  topo = util.Struct(nodes={}, edges=[])
  for vid1, vid2 in util.itertokens(ifname, sep=" ", func=int):
      topo.edges.append((vid1, vid2))
      topo.nodes[vid1] = True
      topo.nodes[vid2] = True
  return topo

def remoteControllerName():
  return "remote"

def localControllerName(vid):
  return "c%d" % vid

def switchName(vid):
  return "s%d" % vid

def hostName(vid):
  return "h%d" % vid
      

def runExperiment(ifname):
  setLogLevel('info')

  print "*** Loading viro topology"
  topo = loadTopology(ifname)

  net = Mininet(controller=POX, switch=OVSKernelSwitch, host=ViroHost)

  print "*** Creating controllers"
  remoteModules = ['viro.core', 'viro.remote.controller', 'viro.remote.dhcpd', 'viro.remote.arpd']
  localModules = ['viro.core', 'viro.local.controller']
  
  port = it.count(6633)
  controllers = util.Struct(remote=None, local={})
  
  name = remoteControllerName()
  controllers.remote = net.addController(name, modules=remoteModules, port=port.next())
  
  for vid in topo.nodes:
    name = localControllerName(vid)
    controllers.local[vid] = net.addController(name, modules=localModules, port=port.next())

  print "*** Creating switches" 
  switches = {}
  for vid in topo.nodes:
    switches[vid] = net.addSwitch(switchName(vid), dpid=util.vid2dpid(vid, 16))

  print "*** Creating hosts"
  hosts = {}
  for vid in topo.nodes:
    hosts[vid] = net.addHost(hostName(vid), ip=None, detachScreen=True, disableIPv6=True, useDHCP=True)


  print "*** Creating links"
  print "*** Adding switch-to-host links"
  for vid, sw in switches.iteritems():
    sw.linkTo(hosts[vid])
  
  print "*** Adding switch-to-switch links"
  for vid1, vid2 in topo.edges:
    switches[vid1].linkTo(switches[vid2])

  print "*** Starting network"
  net.build()
  controllers.remote.start()
  for ctrl in controllers.local.itervalues():
    ctrl.start()
  
  for vid, sw in switches.iteritems():
    sw.start([controllers.remote, controllers.local[vid]])

  print "*** Initializing hosts"
  for h in hosts.itervalues():
    h.initViroHost()
    

  print "*** Running CLI"
  CLI(net)

  print "*** Stopping network"
  net.stop()
  

def main(args):
  runExperiment(args[0])

if __name__ == '__main__':
  main(sys.argv[1:])
