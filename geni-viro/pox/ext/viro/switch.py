import itertools as it
import viro.openflow.of_nicira as vnx
import pox.openflow.libopenflow_01 as of

class Switch(object):
  
  
  def __init__(self, dpid, vid, connection):
    """ Initialize the viro switch object
    dpid         integer for the OVS switch datapath Id
    vid          ViroAddr object
    connection   openflow connection to the OVS
    """
    self.dpid = dpid
    self.vid = vid
    self.connection = connection
    self.hosts = {}
    
    self._nextHostId = it.count(1)
  
  def addHost(self, host):
    self.hosts[host.vid] = host
  
  #Guobao
  def deleteHost(self, host):
    del self.hosts[host.vid]  
  
  def nextHostId(self):
    return self._nextHostId.next()

  
