from pox.core import core
import pox.openflow.libopenflow_01 as of
import pox.lib.packet as pkt
import pox.proto.dhcpd as pox_dhcpd

import viro.openflow.of_nicira as vnx
from viro.remote.controller import RemoteViro

log = core.getLogger()


class DHCPD(pox_dhcpd.DHCPD):
  """ A dhcp server to assign ip addresses to hosts connected to 
  a viro switch """
  
  _core_name = "viro_dhcpd"
  
  def __init__(self, *args, **kwargs):
    pox_dhcpd.DHCPD.__init__(self, *args, **kwargs)
    

  def _handle_ConnectionUp(self, event):
    """ Initialize the viro switch to send dhcp requests to the remote controller """
    if self._install_flow:
      msg = of.ofp_flow_mod()
      
      msg.match = of.ofp_match()
      msg.match.dl_type = pkt.ethernet.IP_TYPE
      msg.priority = 20
      msg.match.nw_proto = pkt.ipv4.UDP_PROTOCOL
      msg.match.tp_src = pkt.dhcp.CLIENT_PORT
      msg.match.tp_dst = pkt.dhcp.SERVER_PORT
      
      action = vnx.nx_action_controller(controller_id=RemoteViro.CONTROLLER_ID)
      msg.actions.append(action)
      
      event.connection.send(msg)
      
  def exec_request(self, event, p, pool):
    self.current_event = event
    pox_dhcpd.DHCPD.exec_request(self, event, p, pool)
    self.current_event = None
      
  def raiseEvent(self, event, *args, **kw):
    if isinstance(event, pox_dhcpd.DHCPLease):
      event.dpid = self.current_event.connection.dpid
    return pox_dhcpd.DHCPD.raiseEvent(self, event, *args, **kw)
      
      
def launch(network="192.168.0.0/24",
           first=1, last=None, count=None,
           ip="192.168.0.254", router=(), dns=()):
  """
  Defaults to serving 192.168.0.1 to 192.168.0.253
  """
  
  def fixint(i):
    i = str(i)
    if i.lower() == "none": return None
    if i.lower() == "true": return None
    return int(i)
  def fix(i):
    i = str(i)
    if i.lower() == "none": return None
    if i.lower() == "true": return None
    if i == '()': return ()
    return i
  
  first,last,count = map(fixint, (first, last, count))
  router, dns = map(fix, (router, dns))

  pool = pox_dhcpd.SimpleAddressPool(network=network, first=first, last=last, count=count)

  core.registerNew(DHCPD, pool=pool, ip_address=ip, router_address=router, dns_address=dns)

  log.debug("DHCP serving a%s", str(pool)[2:-1])
