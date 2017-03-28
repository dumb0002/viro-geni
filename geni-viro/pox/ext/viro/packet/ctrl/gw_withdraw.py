import struct

from pox.lib.packet import packet_base
from pox.lib.packet.packet_utils import *
from viro.packet.vid import VidAddr


class gw_withdraw(packet_base):
  MIN_LEN = 4
  
  def __init__(self, raw=None, prev=None, **kw):
    packet_base.__init__(self)

    self.prev = prev
    self.next = None

    self.failed_gw = 0

    if raw is not None:
      self.parse(raw)

    self._init(kw)

  def _to_str(self):
    s = "[GWWithdraw failed_gw={0}".format(str(self.failed_gw))
    if isinstance(self.next, packet_base):
      return s + str(self.next)    
    return s

  def parse(self, raw):
    assert isinstance(raw, bytes)
    self.raw = raw
    dlen = len(raw)
    if dlen < gw_withdraw.MIN_LEN:
      self.msg('(gw_withdraw parse) warning gw_withdraw packet data too short to parse header: data len %u' % (dlen,))
      return

    hdr = struct.unpack("!I", raw[:gw_withdraw.MIN_LEN])

    self.failed_gw = VidAddr(hdr[0], 0)

    self.parsed = True    
    

  def hdr(self, payload):
    buf = struct.pack("!I", self.failed_gw.sw)
    return buf