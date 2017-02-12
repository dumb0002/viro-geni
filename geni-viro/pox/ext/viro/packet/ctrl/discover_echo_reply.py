import struct

from pox.lib.packet import packet_base
from pox.lib.packet.packet_utils import *
from viro.packet.vid import VidAddr


class discover_echo_reply(packet_base):
  MIN_LEN = 1
  
  def __init__(self, raw=None, prev=None, **kw):
    packet_base.__init__(self)

    self.prev = prev
    self.next = None

    self.null = 0

    if raw is not None:
      self.parse(raw)

    self._init(kw)

  def _to_str(self):
    s = "[DiscoverEchoReply]"
    if isinstance(self.next, packet_base):
      return s + str(self.next)    
    return s

  def parse(self, raw):
    assert isinstance(raw, bytes)
    self.raw = raw
    dlen = len(raw)
    if dlen < discover_echo_reply.MIN_LEN:
      self.msg('(discover_echo_reply parse) warning discover_echo_reply packet data too short to parse header: data len %u' % (dlen,))
      return

    hdr = struct.unpack("!B", raw[:discover_echo_reply.MIN_LEN])

    if hdr[0] != 0:
      raise Exception("discover_echo_reply must contain a null byte")

    self.null = 0
    self.parsed = True    
    

  def hdr(self, payload):
    buf = struct.pack("!B", self.null)
    return buf