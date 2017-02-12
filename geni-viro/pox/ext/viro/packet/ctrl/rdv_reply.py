import struct

from pox.lib.packet import packet_base
from pox.lib.packet.packet_utils import *
from viro.packet.vid import VidAddr


class rdv_reply(packet_base):
  MIN_LEN = 8
  
  def __init__(self, raw=None, prev=None, **kw):
    packet_base.__init__(self)

    self.prev = prev
    self.next = None

    self.bucket_dist = 0
    self.gw = 0    

    if raw is not None:
      self.parse(raw)

    self._init(kw)

  def _to_str(self):
    s = "[RDVReply bucket_dist={0}, gw={1}".format(self.bucket_dist, str(self.gw))
    if isinstance(self.next, packet_base):
      return s + str(self.next)    
    return s

  def parse(self, raw):
    assert isinstance(raw, bytes)
    self.raw = raw
    dlen = len(raw)
    if dlen < rdv_reply.MIN_LEN:
      self.msg('(rdv_reply parse) warning rdv_reply packet data too short to parse header: data len %u' % (dlen,))
      return

    hdr = struct.unpack("!II", raw[:rdv_reply.MIN_LEN])

    self.bucket_dist = hdr[0]
    self.gw = VidAddr(hdr[1], 0)

    self.parsed = True    
    

  def hdr(self, payload):
    buf = struct.pack("!II", self.bucket_dist, self.gw.sw)
    return buf