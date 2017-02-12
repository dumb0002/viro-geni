import struct
from pox.core import core
from pox.lib.packet import packet_base
from pox.lib.packet import ethernet

from pox.lib.packet.packet_utils import *
import pox.lib.packet.packet_utils as pktutils

from vid import VidAddr 
from viro_ctrl import viroctrl

log = core.getLogger()

pktutils._ethtype_to_str[0x0802] = "VIRO" 

class viro(packet_base):

  VIRO_TYPE = 0x0802

  MIN_LEN = 22

  def __init__(self, raw=None, prev=None, **kw):
    packet_base.__init__(self)

    self.prev = prev
    self.next = None

    self.src = None
    self.dst = None
    self.fd = VidAddr(0, 0)
    self.next_eth_type = 0

    if raw is not None:
      self.parse(raw)

    self._init(kw)

  def _to_str(self):
    s = "[VIRO src_sw={0:#04x} src_host={1:#04x} " \
        "dst_sw={2:#04x} dst_host={3:#04x} " \
        "fd_sw={4:#04x} fd_host={5:#04x} next_eth_type={6}]".format(
          self.src.sw, self.src.host,
          self.dst.sw, self.dst.host,
          self.fd.sw, self.fd.host, ethtype_to_str(self.next_eth_type))
    
    if isinstance(self.next, packet_base):
      return s + str(self.next)
    return s
  
  def parse(self, raw):
    assert isinstance(raw, bytes)
    self.raw = raw
    dlen = len(raw)
    if dlen < viro.MIN_LEN:
      self.msg('(viro parse) warning VIRO packet data too short to parse header: data len %u' % (dlen,))
      return

    hdr = struct.unpack("!IHIHHIHH", raw[:viro.MIN_LEN])

    self.dst = VidAddr(hdr[0], hdr[1])
    self.src = VidAddr(hdr[2], hdr[3])
    
    eth_type = hdr[4]
    assert eth_type == viro.VIRO_TYPE
    
    self.fd = VidAddr(hdr[5], hdr[6])
    self.next_eth_type = hdr[7]

    self.parsed = True
    
    if self.next_eth_type == viroctrl.VIRO_CTRL_TYPE:
      self.next = viroctrl(raw[viro.MIN_LEN:], self)
    else:
      self.next = ethernet.parse_next(self, self.next_eth_type, raw, viro.MIN_LEN)

  @property
  def effective_ethertype(self):
    return self.next_eth_type

  @property
  def type(self):
    return viro.VIRO_TYPE
    

  def hdr(self, payload):
    buf = struct.pack("!IHIHHIHH", self.dst.sw, self.dst.host,
                      self.src.sw, self.src.host,
                      viro.VIRO_TYPE, self.fd.sw, self.fd.host, self.next_eth_type)
    return buf
