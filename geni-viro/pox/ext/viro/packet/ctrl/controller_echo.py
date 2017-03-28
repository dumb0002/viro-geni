import struct

from pox.lib.packet import packet_base
from pox.lib.packet.packet_utils import *
from viro.packet.vid import VidAddr


class controller_echo(packet_base):
  MIN_LEN = 8
  
  def __init__(self, raw=None, prev=None, **kw):
    packet_base.__init__(self)

    self.prev = prev
    self.next = None

    self.from_controller_id = 0
    self.to_controller_id = 0
    self.vid = None

    if raw is not None:
      self.parse(raw)

    self._init(kw)

  def _to_str(self):
    s = "[ControllerEcho from_controller_id={0}, to_controller_id={1}, vid={2}]".format(self.from_controller_id, self.to_controller_id, str(self.vid))
    if isinstance(self.next, packet_base):
      return s + str(self.next)    
    return s

  def parse(self, raw):
    assert isinstance(raw, bytes)
    self.raw = raw
    dlen = len(raw)
    if dlen < controller_echo.MIN_LEN:
      self.msg('(controller_echo parse) warning controller_echo packet data too short to parse header: data len %u' % (dlen,))
      return

    hdr = struct.unpack("!BBIH", raw[:controller_echo.MIN_LEN])

    self.from_controller_id = hdr[0]
    self.to_controller_id = hdr[1]
    self.vid = VidAddr(hdr[2], hdr[3])

    self.parsed = True    
    

  def hdr(self, payload):
    buf = struct.pack("!BB", self.from_controller_id, self.to_controller_id) + self.vid.raw
    return buf
