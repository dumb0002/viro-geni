from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.util import str_to_bool
from pox.lib.util import initHelper
from pox.lib.addresses import IPAddr, EthAddr

import viro.openflow.of_viro as vof

log = core.getLogger()

class ViroSwitch(EventMixin):
  """
  Waits for OpenFlow switches to connect and makes them viro switches.
  """

  def __init__ (self):
    self.listenTo(core.openflow)

  def _handle_ConnectionUp (self, event):
    log.debug("Connection %s %s" % (event.connection, dpidToStr(event.dpid)))

    self.dpid = event.dpid
    self.ports = {}

    for p in event.ofp.ports:
      if p.port_no != of.OFPP_CONTROLLER and p.port_no != of.OFPP_LOCAL:
        self.ports[p.port_no] = {'hw_addr': p.hw_addr, 'name': p.name}
        
    msg = of.ofp_flow_mod()
    msg.match = of.ofp_match()
    msg.match.in_port = 1
    msg.idle_timeout = 0
    msg.hard_timeout = 0
    msg.buffer_id = of.NO_BUFFER

    case = 2

    if case == 1:
      msg.actions.append(vof.viro_action_pop_fd())
      msg.actions.append(of.ofp_action_dl_addr.set_dst(dl_addr = EthAddr("01:01:01:01:01:01")))
      # msg.actions.append(of.ofp_action_nw_addr.set_dst(nw_addr = IPAddr("10.0.0.1")))
    elif case == 2:
      msg.actions.append(vof.viro_action_push_fd(fd = vof.viro_addr(0x01, 0x02)))
          
      msg.actions.append(vof.viro_action_vid_sw.set_fd(0x0a0b0c0d))
      msg.actions.append(vof.viro_action_vid_host.set_fd(0x0e0f))
      
      msg.actions.append(vof.viro_action_vid_sw.set_dst(0x01020304))
      msg.actions.append(vof.viro_action_vid_host.set_dst(0x1122))
      
      msg.actions.append(vof.viro_action_vid_sw.set_src(0x05060708))
      msg.actions.append(vof.viro_action_vid_host.set_src(0x3344))
    
    
    msg.actions.append(of.ofp_action_output(port = 2))
    
    event.connection.send(msg)


  def _handle_PacketIn (self, event):
    log.debug("PacketIn")
    # packet = event.parse()





def launch ():
  core.registerNew(ViroSwitch)
