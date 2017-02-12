import struct

from pox.lib.packet import packet_base
from pox.lib.packet.packet_utils import *
from viro.packet.vid import VidAddr


class rdv_query(packet_base):
  MIN_LEN = 4
  
  def __init__(self, raw=None, prev=None, **kw):
    packet_base.__init__(self)

    self.prev = prev
    self.next = None

    self.bucket_dist = 0

    if raw is not None:
      self.parse(raw)

    self._init(kw)

  def _to_str(self):
    s = "[RDVQuery bucket_dist={0}".format(self.bucket_dist)
    if isinstance(self.next, packet_base):
      return s + str(self.next)    
    return s

  def parse(self, raw):
    assert isinstance(raw, bytes)
    self.raw = raw
    dlen = len(raw)
    if dlen < rdv_query.MIN_LEN:
      self.msg('(rdv_query parse) warning rdv_query packet data too short to parse header: data len %u' % (dlen,))
      return

    hdr = struct.unpack("!I", raw[:rdv_query.MIN_LEN])

    self.bucket_dist = hdr[0]

    self.parsed = True    
    

  def hdr(self, payload):
    buf = struct.pack("!I", self.bucket_dist)
    return buf