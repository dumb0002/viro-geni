import viro.openflow.of_nicira as vnx
import pox.openflow.libopenflow_01 as of
from viro.packet.vid import VidAddr

from viro.packet.viro import viro
from viro.packet.viro_ctrl import viroctrl

from pox.lib.packet.ethernet import ethernet
import viro.openflow.of_viro as vof

def flood(packet):
  """ Create openflow flood message """
  msg = of.ofp_packet_out()
  msg.data = packet.pack()
  msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
  
  return msg

def packetOut(packet, port):
  msg = of.ofp_packet_out()
  msg.data = packet.pack()
  msg.actions.append(of.ofp_action_output(port = port))
  
  return msg
  
def controllerEcho(toCtrlId, packet):
  """ Sends a message from local viro to the remote viro """
  msg = of.ofp_packet_out()
  msg.data = packet.pack()
  msg.actions.append(vnx.nx_action_controller(controller_id = toCtrlId))
  msg.actions.append(of.ofp_action_output(port = of.OFPP_NONE))
  
  return msg


def ofpControllerId(cid):
  """ Updates the OVS controller Id associated with connection """
  msg = vnx.nx_controller_id(controller_id=cid)
  
  return msg


def ofpFlowModTableId():
  """ Enables the OF tableId extension """
  msg = vnx.nx_flow_mod_table_id()
  return msg

def ctrlPktsLocalViroPacketIn(toCtrlId):
  """ Match on viroctrl packets and generate packetIns to the local controller """
  #fm = of.ofp_flow_mod()
  
  fm = vnx.nx_flow_mod()

  # FIXME note that here we match on all VIRO packet
  # i.e. viroctrl packets and viro data packet will be 
  # sent to the local controller. A simple solution to this
  # is to set the priority to low value for the VIRO control 
  # packet, and therefore VIRO data packet will match on higher
  # priority rules without touching this rule
  # fm.match.dl_type = viro.VIRO_TYPE
  # Guobao
  fm.match.eth_type = viro.VIRO_TYPE
  fm.table_id = 1
  fm.priority = 10
  fm.command = of.OFPFC_ADD
  fm.idle_timeout = 0
  fm.hard_timeout = of.OFP_FLOW_PERMANENT
  fm.buffer_id = of.NO_BUFFER
  fm.actions.append(vnx.nx_action_controller(controller_id = toCtrlId))
  fm.actions.append(of.ofp_action_output(port = of.OFPP_NONE))

  return fm



def IPv4LocalViroPacketIn(toCtrlId):
  """ Match on IPv4 packets and generate packetIns to the local controller """
  #fm = of.ofp_flow_mod()

  fm = vnx.nx_flow_mod()

  # FIXME match on IPv4 packet and sends it to the local controller, we need to
  # extend this to handle IPv6 packets
  # fm.match.dl_type = ethernet.IP_TYPE
  # Guobao
  fm.match.eth_type = ethernet.IP_TYPE
  fm.table_id = 0
  fm.priority = 10
  fm.command = of.OFPFC_ADD
  fm.idle_timeout = 0
  fm.hard_timeout = of.OFP_FLOW_PERMANENT
  fm.buffer_id = of.NO_BUFFER
  fm.actions.append(vnx.nx_action_controller(controller_id = toCtrlId))
  fm.actions.append(of.ofp_action_output(port = of.OFPP_NONE))

  return fm

def FallBack(nextTable):
  msg = vnx.nx_flow_mod()
  msg.priority = 1
  msg.actions.append(vnx.nx_action_resubmit.resubmit_table(nextTable))
  return msg

def pushRoutingTable(dst_vid, dst_vid_mask, Outport):

    msg = vnx.nx_flow_mod()
    msg.table_id = 1
    msg.priority = 15
    msg.match.eth_type = viro.VIRO_TYPE
    msg.match.viro_dst_sw = dst_vid
    msg.match.viro_dst_sw_mask = dst_vid_mask
	
    #msg.match.viro_dst_host = 0xdcba
    #msg.match.viro_src_sw = 0x11110000
    #msg.match.viro_src_sw_mask = 0xffff0000
    #msg.match.viro_src_host = 0xabcd
    #msg.match.viro_fd_sw = 0x11111111
    #msg.match.viro_fd_sw_mask = 0xffffffff
    #msg.match.viro_fd_host = 0x3333
	
    #msg.actions.append(vof.viro_action_push_fd(fd = VidAddr(0x01, 0x02)))
    #msg.actions.append(vof.viro_action_vid_sw.set_fd(0x0a0b0c0d))
    #msg.actions.append(vof.viro_action_vid_host.set_fd(0x0e0f))
      
    #msg.actions.append(vof.viro_action_vid_sw.set_dst(0x01020304))
    #msg.actions.append(vof.viro_action_vid_host.set_dst(0x1122))
      
    #msg.actions.append(vof.viro_action_vid_sw.set_src(0x05060708))
    #msg.actions.append(vof.viro_action_vid_host.set_src(0x3344))
	
    msg.actions.append(of.ofp_action_output(port = Outport))
	
    return msg

def pushRoutingTableETH(dst_vid, dst_vid_mask, Outport):
  fake_dst_mac = VidAddr(dst_vid, 0x00)
  fake_dst_mac_mask = VidAddr(dst_vid_mask, 0x00)

  msg = vnx.nx_flow_mod()
  msg.table_id = 1
  msg.priority = 15
  msg.match.eth_type = ethernet.IP_TYPE
  msg.match.eth_dst = fake_dst_mac.to_raw()
  msg.match.eth_dst_mask = fake_dst_mac_mask.to_raw()

  msg.actions.append(of.ofp_action_output(port = Outport))

  return msg

def encapsulate(src_mac, src_vid, dst_mac, dst_vid):
    msg = vnx.nx_flow_mod()
    msg.table_id = 0
    msg.priority = 15
    msg.match.eth_type = ethernet.IP_TYPE
    msg.match.eth_src = src_mac
    msg.match.eth_dst = dst_mac
    
    msg.actions.append(vof.viro_action_push_fd(fd = VidAddr(0x08, 0x0a)))
    msg.actions.append(vof.viro_action_vid_sw.set_src(src_vid.sw))
    msg.actions.append(vof.viro_action_vid_host.set_src(src_vid.host))

    msg.actions.append(vof.viro_action_vid_sw.set_dst(dst_vid.sw))
    msg.actions.append(vof.viro_action_vid_host.set_dst(dst_vid.host))

    msg.actions.append(vnx.nx_action_resubmit.resubmit_table(1))

    # msg.actions.append(of.ofp_action_output(port = Outport))
   
    return msg

def decapsulate(dst_mac, dst_vid, Outport):
    msg = vnx.nx_flow_mod()
    msg.match.eth_type = viro.VIRO_TYPE
    msg.match.viro_dst_sw = dst_vid.sw
    msg.match.viro_dst_host = dst_vid.host

    msg.actions.append(vof.viro_action_pop_fd())
    msg.actions.append(of.ofp_action_dl_addr.set_dst(dst_mac))
    msg.actions.append(of.ofp_action_output(port = Outport))
    
    return msg




def rewriteMac(src_mac, dst_mac, Outport):
    msg = vnx.nx_flow_mod()
    msg.table_id = 0
    msg.priority = 16
    msg.match.eth_type = ethernet.IP_TYPE
    msg.match.eth_src = src_mac
    msg.match.eth_dst = dst_mac
   
    msg.actions.append(of.ofp_action_output(port = Outport))
    
    return msg



#def rewriteMac(src_mac, dst_mac, Outport):
    #msg = vnx.nx_flow_mod()
    #msg.table_id = 0
    #msg.priority = 16
    #msg.match.eth_type = ethernet.IP_TYPE
    #msg.match.eth_src = src_mac
    #msg.match.eth_dst = dst_mac
   
    #msg.actions.append(of.ofp_action_output(port = Outport))
    
    #return msg



#def rewriteMac(src_vid, dst_vid, dst_mac, Outport):
    #msg = vnx.nx_flow_mod()
    #msg.table_id = 0
    #msg.priority = 16
    #msg.match.eth_type = ethernet.IP_TYPE
    #msg.match.eth_dst = dst_vid
    #msg.match.viro_dst_sw = dst_vid.sw
    #msg.match.viro_dst_host = dst_vid.host

    # msg.actions.append(vof.viro_action_pop_fd())
    #msg.actions.append(vof.viro_action_vid_sw.set_src(src_vid.sw))
    #msg.actions.append(vof.viro_action_vid_host.set_src(src_vid.host))
    #msg.actions.append(of.ofp_action_dl_addr.set_dst(dst_mac))
    #msg.actions.append(of.ofp_action_output(port = Outport))
    
    #return msg
