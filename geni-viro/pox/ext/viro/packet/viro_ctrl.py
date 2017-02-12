import struct
from pox.lib.packet import packet_base
from pox.lib.packet import ethernet
from pox.lib.packet.packet_utils import *
import pox.lib.packet.packet_utils as pktutils

from ctrl import *

pktutils._ethtype_to_str[0x0803] = "VIROCTRL"

class viroctrl(packet_base):

  VIRO_CTRL_TYPE = 0x0803
  
  # Control packets codes
  # Packet OPCode is the first 2-bytes in the control packet
  
  # Controller-to-controller hello packets
  CONTROLLER_ECHO     = 0x0001

  # Remote-to-Local controller host vid/mac mapping info.
  LOCAL_HOST          = 0x8000
  VID_REQUEST         = 0x9000
  HOST_WITHDRAW       = 0X0002

  # VIRO routing control packets
  RDV_PUBLISH         = 0x1000
  RDV_QUERY           = 0x2000
  RDV_REPLY           = 0x3000
  RDV_WITHDRAW        = 0x7000
  GW_WITHDRAW         = 0x6000
  
  # Neighbor discovery hello packets
  DISC_ECHO_REQ       = 0x4000
  DISC_ECHO_REPLY     = 0x5000  

  MIN_LEN = 2

  def __init__(self, raw=None, prev=None, **kw):
    packet_base.__init__(self)

    self.prev = prev
    self.next = None

    self.op = 0

    if raw is not None:
      self.parse(raw)

    self._init(kw)

  def _to_str(self):
    s = "[VIROCTRL op={0:#04x}]".format(self.op)
    if isinstance(self.next, packet_base):
      return s + str(self.next)    
    return s

  def parse(self, raw):
    assert isinstance(raw, bytes)
    self.raw = raw
    dlen = len(raw)
    if dlen < viroctrl.MIN_LEN:
      self.msg('(viroctrl parse) warning VIROCTRL packet data too short to parse header: data len %u' % (dlen,))
      return

    hdr = struct.unpack("!H", raw[:viroctrl.MIN_LEN])

    self.op = hdr[0]

    self.parsed = True
    
    if self.op == viroctrl.CONTROLLER_ECHO:
      self.next = controller_echo(raw=raw[viroctrl.MIN_LEN:], prev=self)

    elif self.op == viroctrl.LOCAL_HOST:
      self.next = local_host(raw=raw[viroctrl.MIN_LEN:], prev=self)

    elif self.op == viroctrl.VID_REQUEST:
      self.next = vid_request(raw=raw[viroctrl.MIN_LEN:], prev=self)

    elif self.op == viroctrl.HOST_WITHDRAW:
      self.next = host_withdraw(raw=raw[viroctrl.MIN_LEN:], prev=self)

    elif self.op == viroctrl.RDV_PUBLISH:
      self.next = rdv_publish(raw=raw[viroctrl.MIN_LEN:], prev=self)

    elif self.op == viroctrl.RDV_QUERY:
      self.next = rdv_query(raw=raw[viroctrl.MIN_LEN:], prev=self)

    elif self.op == viroctrl.RDV_REPLY:
      self.next = rdv_reply(raw=raw[viroctrl.MIN_LEN:], prev=self)

    elif self.op == viroctrl.RDV_WITHDRAW:
      self.next = rdv_withdraw(raw=raw[viroctrl.MIN_LEN:], prev=self)

    elif self.op == viroctrl.GW_WITHDRAW:
      self.next = gw_withdraw(raw=raw[viroctrl.MIN_LEN:], prev=self)

    elif self.op == viroctrl.DISC_ECHO_REQ:
      self.next = discover_echo_request(raw=raw[viroctrl.MIN_LEN:], prev=self)

    elif self.op == viroctrl.DISC_ECHO_REPLY:
      self.next = discover_echo_reply(raw=raw[viroctrl.MIN_LEN:], prev=self)

    else:
      self.payload = raw[viroctrl.MIN_LEN:]
    

  def hdr(self, payload):
    buf = struct.pack("!H", self.op)
    return buf
