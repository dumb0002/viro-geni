from pox.core import core
import struct
from viro.packet.viro import viro
from viro.packet.viro_ctrl import viroctrl
from viro.packet.vid import VidAddr
from viro.packet.ctrl import *
from pox.lib.packet import *

log = core.getLogger()
vidNull = VidAddr(0, 0)

def controlPacket(srcVid, dstVid, fdVid, op, payload):
  """ Create a viro control packet """
  ctrl = viroctrl(op=op)
  ctrl.payload = payload
  
  packet = viro(src=srcVid, dst=dstVid, fd=fdVid)
  packet.next_eth_type = viroctrl.VIRO_CTRL_TYPE
  packet.payload = ctrl
  
  return packet

def controllerEcho(fromCtrlId, toCtrlId, vid):
  """ Create a controller-to-controller echo packet """
  payload = controller_echo(from_controller_id=fromCtrlId, to_controller_id=toCtrlId, vid=vid)
  return controlPacket(vidNull, vidNull, vidNull,
                       viroctrl.CONTROLLER_ECHO,
                       payload)

def discoverEchoRequest(srcVid):
  """ Create a viro discovery echo request packet """
  return controlPacket(srcVid, vidNull, vidNull,
                       viroctrl.DISC_ECHO_REQ,
                       discover_echo_request())

def discoverEchoReply(srcVid, dstVid):
  """ Create a viro discovery echo reply packet """
  return controlPacket(srcVid, dstVid, vidNull,
                       viroctrl.DISC_ECHO_REPLY,
                       discover_echo_reply())

def gatewayWithdraw(srcVid, dstVid, failedGw):
  """ Create a viro gateway withdraw packet """
  return controlPacket(srcVid, dstVid, vidNull,
                       viroctrl.GW_WITHDRAW,
                       gw_withdraw(failed_gw=failedGw))

def rdvPublish(srcVid, dstVid, nexthop):
  """ Create a viro gateway withdraw packet """
  return controlPacket(srcVid, dstVid, vidNull,
                       viroctrl.RDV_PUBLISH,
                       rdv_publish(vid=nexthop))

def rdvQuery(srcVid, dstVid, level):
  """ Create a viro gateway withdraw packet """
  return controlPacket(srcVid, dstVid, vidNull,
                       viroctrl.RDV_QUERY,
                       rdv_query(bucket_dist=level))
  
def rdvReply(srcVid, dstVid, k, gw):
  """ Create a viro gateway withdraw packet """
  return controlPacket(srcVid, dstVid, vidNull,
                       viroctrl.RDV_REPLY,
                       rdv_reply(bucket_dist=k, gw=gw))

def rdvWithdraw(srcVid, dstVid, k, gw):
  """ Create a viro gateway withdraw packet """
  return controlPacket(srcVid, dstVid, vidNull,
                       viroctrl.RDV_WITHDRAW,
                       rdv_withdraw(bucket_dist=k, gw=gw))


def localhost(mac, ip, port, vid):
  """ Create a viro local host packet """
  payload = local_host(mac=mac, ip=ip, port=port, vid=vid)
  return controlPacket(vidNull, vidNull, vidNull,
                       viroctrl.LOCAL_HOST,
                       payload)


def vidRequest(mac, ip, port):
  """ Create a viro vid request packet """
  payload = vid_request(mac=mac, ip=ip, port=port)
  return controlPacket(vidNull, vidNull, vidNull,
                       viroctrl.VID_REQUEST,
                       payload)

  
def ethernetPkt(ethtype, srMac, dstMac, dataPacket):
     """ Create a viro local host packet """
     packet = ethernet(type = ethtype, src = srMac , dst = dstMac)
     packet.set_payload(dataPacket)
     return  packet 


def ViroPacket(srcVid, dstVid, fdvid, etype, payload):
  """ Create a viro  packet """

  packet = viro(src=srcVid, dst=dstVid, fd= vidNull)
  packet.next_eth_type = etype
  packet.payload = payload

  return packet

