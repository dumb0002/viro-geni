import struct

from pox.lib.packet import packet_base
from pox.lib.packet.packet_utils import *
from viro.packet.vid import VidAddr
from pox.lib.addresses import *


class host_withdraw(packet_base):
  MIN_LEN = 4
  
  def __init__(self, raw=None, prev=None, **kw):
    packet_base.__init__(self)

    self.prev = prev
    self.next = None

    self.failed_host = 0

    if raw is not None:
      self.parse(raw)

    self._init(kw)

  def _to_str(self):
    s = "[HostWithdraw failed_host={0}]".format(self.failed_host)
    if isinstance(self.next, packet_base):
      return s + str(self.next)    
    return s

  def parse(self, raw):
    assert isinstance(raw, bytes)
    self.raw = raw
    dlen = len(raw)
    if dlen < host_withdraw.MIN_LEN:
      self.msg('(host_withdraw parse) warning host_withdraw packet data too short to parse header: data len %u' % (dlen,))
      return

    hdr = struct.unpack("!I", raw[:host_withdraw.MIN_LEN])

    self.failed_host = IPAddr(hdr[0])

    self.parsed = True    
    

  def hdr(self, payload):
    buf = self.failed_host.raw
    return buf
