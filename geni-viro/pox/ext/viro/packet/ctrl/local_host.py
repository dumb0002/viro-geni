import struct

from pox.lib.packet import packet_base
from pox.lib.packet.packet_utils import *
from viro.packet.vid import VidAddr
from pox.lib.addresses import *
from viro.host import Host


class local_host(packet_base):
  MIN_LEN = 20
  
  def __init__(self, raw=None, prev=None, **kw):
    packet_base.__init__(self)

    self.prev = prev
    self.next = None

    self.mac = 0
    self.ip = 0
    self.vid = 0
    self.port = 0
    self.host = 0    

    if raw is not None:
      self.parse(raw)

    self._init(kw)

  def _to_str(self):
    s = "[LOCAL HOST: mac={0}, vid={1}, ip={2}, port={3}]".format(self.mac, str(self.vid), self.ip, self.port)
    if isinstance(self.next, packet_base):
      return s + str(self.next)    
    return s

  def parse(self, raw):
    assert isinstance(raw, bytes)
    self.raw = raw
    dlen = len(raw)
    if dlen < local_host.MIN_LEN:
      self.msg('(local_host) warning local_host packet data too short to parse header: data len %u' % (dlen,))
      return

    
    hdr = struct.unpack("!IIHI", raw[6:local_host.MIN_LEN])
    mac = raw[:6]
   
    self.mac = EthAddr(mac)
    self.ip =  IPAddr(hdr[0])
    self.vid = VidAddr(hdr[1], hdr[2])
    self.port = hdr[3]
    self.host= Host(self.mac, self.ip, self.vid, self.port, None)
    

    self.parsed = True    
    

  def hdr(self, payload):
    buf =  self.mac.raw + self.ip.raw + self.vid.raw + struct.pack("!I", self.port)

    return buf
