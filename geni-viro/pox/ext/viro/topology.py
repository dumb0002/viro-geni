from viro.switch import Switch
from viro.host import Host

class Topology(object):
  
  def __init__(self):
    self._dpids = {}
    self._vids = {}
    
    self._ips = {}
    self._vids = {}
    self._macs = {}
    self._ports = {}
    

  def addSwitch(self, sw):
    self._dpids[sw.dpid] = sw
    self._vids[sw.vid] = sw
    return sw
  
  def findSwitchByDpid(self, dpid):
    try:
      return self._dpids[dpid]
    except KeyError:
      return None
  
  def findSwitchByVid(self, vid):
    try:
      return self._vids[vid]
    except KeyError:
      return None
    
  def switches(self):
    for sw in self._dpids.itervalues():
      yield sw
    
  def addHost(self, host):
    self._ips[host.ip] = host
    self._vids[host.vid] = host
    self._macs[host.mac] = host
    self._ports[host.port] = host
    return host
  
  #Guobao
  def deleteHost(self, host):
    del self._ips[host.ip]
    del self._vids[host.vid]
    del self._macs[host.mac]
    del  self._ports[host.port]
  
  def findHostByIp(self, ip):
    try:
      return self._ips[ip]
    except KeyError:
      return None
  
  def findHostByMac(self, mac):
    try:
      return self._macs[mac]
    except KeyError:
      return None
  
  def findHostByVid(self, vid):
    try:
      return self._vids[vid]
    except KeyError:
      return None
      
  def deleteHostByIP(self, ip):
      host = self._ips[ip]
      self.deleteHost(host)

  def findHostByPort(self, port):
    try:
      return self._ports[port]
    except KeyError:
      return None