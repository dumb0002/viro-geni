import struct

from pox.lib.packet import packet_base
from pox.lib.packet.packet_utils import *
from viro.packet.vid import VidAddr


class rdv_publish(packet_base):
  MIN_LEN = 4
  
  def __init__(self, raw=None, prev=None, **kw):
    packet_base.__init__(self)

    self.prev = prev
    self.next = None

    self.vid = 0

    if raw is not None:
      self.parse(raw)

    self._init(kw)

  def _to_str(self):
    s = "[RDVPublish vid={0}".format(str(self.vid))
    if isinstance(self.next, packet_base):
      return s + str(self.next)    
    return s

  def parse(self, raw):
    assert isinstance(raw, bytes)
    self.raw = raw
    dlen = len(raw)
    if dlen < rdv_publish.MIN_LEN:
      self.msg('(rdv_publish parse) warning rdv_publish packet data too short to parse header: data len %u' % (dlen,))
      return

    hdr = struct.unpack("!I", raw[:rdv_publish.MIN_LEN])

    self.vid = VidAddr(hdr[0], 0)

    self.parsed = True    
    

  def hdr(self, payload):
    buf = struct.pack("!I", self.vid.sw)
    return buf