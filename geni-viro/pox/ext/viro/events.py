from pox.lib.revent import *

class ViroSwitchUp(Event):
  """ Viro switch is up event """
  def __init__(self, connection, ofp):
    Event.__init__(self)
    self.dpid = connection.dpid
    self.connection = connection
    self.ofp = ofp

class ViroSwitchDown(Event):
  """ Viro switch is down event """
  def __init__(self, dpid):
    Event.__init__(self)
    self.dpid = dpid

class ViroPacketIn(Event):
  """ Base class for all packetIn events """
  def __init__(self, dpid, port, packet):
    Event.__init__(self)
    self.dpid = dpid
    self.port = port 
    self.packet = packet


class ViroSwitchPortStatus(Event):
  """ Viro switch port status event """
  def __init__(self, connection, ofp):
    Event.__init__(self)
    self.connection = connection
    self.dpid = connection.dpid
    self.ofp = ofp
   
    
class ViroPacketInIP(ViroPacketIn):
  """ IPv4 packetIn event """
  def __init__(self, *args, **kwargs):
    ViroPacketIn.__init__(self, *args, **kwargs)

class ViroPacketInIPV6(ViroPacketIn):
  """ IPv6 packetIn event """
  def __init__(self, *args, **kwargs):
    ViroPacketIn.__init__(self, *args, **kwargs)

class ViroPacketInARP(ViroPacketIn):
  """ ARP packetIn event """
  def __init__(self, *args, **kwargs):
    ViroPacketIn.__init__(self, *args, **kwargs)

class ViroPacketInLLDP(ViroPacketIn):
  """ LLDP packetIn event """
  def __init__(self, *args, **kwargs):
    ViroPacketIn.__init__(self, *args, **kwargs)

class ViroPacketInVIROData(ViroPacketIn):
  """ VIRO packetIn event """
  def __init__(self, *args, **kwargs):
    ViroPacketIn.__init__(self, *args, **kwargs)


class ViroPacketInVIROCtrl(ViroPacketIn):
  """ VIRO packetIn event """
  def __init__(self, *args, **kwargs):
    ViroPacketIn.__init__(self, *args, **kwargs)


