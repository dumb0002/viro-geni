from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.packet.ethernet import ethernet
from viro.packet.viro import viro
from viro.packet.viro_ctrl import viroctrl

from viro.events import *

log = core.getLogger()


class ViroSwitch(EventMixin):
  """
  Waits for OpenFlow switches to connect and raises events correspondigly
  """

  _eventMixin_events = set([
     ViroSwitchUp, ViroSwitchDown,
     ViroPacketInIP, ViroPacketInIPV6,
     ViroPacketInARP, ViroPacketInLLDP,
     ViroPacketInVIROCtrl, ViroPacketInVIROData,
     ViroSwitchPortStatus
  ])

  _core_name = "viro_core"

  def __init__(self):
    EventMixin.__init__(self)
    core.listen_to_dependencies(self)

  def _handle_openflow_ConnectionUp(self, event):
    log.debug("Connection Up %s %s" % (event.connection, dpidToStr(event.dpid)))
    self.raiseEvent(ViroSwitchUp, event.connection, event.ofp)

  def _handle_openflow_ConnectionDown(self, event):
    log.debug("Connection Down %s", event.connection)
    self.raiseEvent(ViroSwitchDown, event.dpid)

  def _handle_openflow_PortStatus(self, event):
    log.debug("Port Status Event from Switch: %s", dpidToStr(event.dpid))
    self.raiseEvent(ViroSwitchPortStatus, event.connection, event.ofp)

  def _handle_openflow_PacketIn(self, event):    
    dpid = event.dpid
    packet = event.parsed
    port = event.port
    etype = packet.type
    
    log.debug("PacketIn from %s, EtherType=%#x", dpidToStr(event.dpid), etype)    
    
    if etype == ethernet.IP_TYPE:
      self.raiseEvent(ViroPacketInIP, dpid, port, packet)      
    elif etype == ethernet.IPV6_TYPE:
      self.raiseEvent(ViroPacketInIPV6, dpid, port, packet)
    elif etype == ethernet.LLDP_TYPE:
      self.raiseEvent(ViroPacketInLLDP, dpid, port, packet)
    elif etype == ethernet.ARP_TYPE:
      self.raiseEvent(ViroPacketInARP, dpid, port, packet)
    elif etype == viro.VIRO_TYPE:
      packet = viro(packet.raw)
      viro_payload = packet.payload
      if isinstance(viro_payload, viroctrl):
        self.raiseEvent(ViroPacketInVIROCtrl, dpid, port, packet)
      else:
        self.raiseEvent(ViroPacketInVIROData, dpid, port, packet)
    else:
      log.debug("Unknown packet type %#x", etype)


def launch():
  core.registerNew(ViroSwitch)
