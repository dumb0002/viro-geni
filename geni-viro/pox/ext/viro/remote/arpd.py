from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.proto.arp_helper import *

import viro.openflow.of_nicira as vnx
from viro.remote.controller import RemoteViro

log = core.getLogger()

class ARPD(ARPHelper):
  
  _eventMixin_events = set([ARPRequest])
  
  _core_name = "viro_arpd"
  

  def __init__(self):
    ARPHelper.__init__(self, no_flow=False, eat_packets=False)    

  def _handle_ConnectionUp(self, event):
    """ Initialize the viro switch to send arp requests to the remote controller """
    if self._install_flow:
      fm = of.ofp_flow_mod()
      #Guobao
      fm.priority = 20
      fm.match.dl_type = ethernet.ARP_TYPE
      fm.actions.append(vnx.nx_action_controller(controller_id=RemoteViro.CONTROLLER_ID))
      event.connection.send(fm)
    
  
def launch():
  core.registerNew(ARPD)
  

