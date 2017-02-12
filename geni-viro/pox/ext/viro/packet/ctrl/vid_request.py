import struct

from pox.lib.packet import packet_base
from pox.lib.packet.packet_utils import *
from viro.packet.vid import VidAddr
from pox.lib.addresses import *



class vid_request(packet_base):
  MIN_LEN = 14
  
  def __init__(self, raw=None, prev=None, **kw):
    packet_base.__init__(self)

    self.prev = prev
    self.next = None

    self.mac = 0
    self.ip = 0
    self.port = 0        

    if raw is not None:
      self.parse(raw)

    self._init(kw)

  def _to_str(self):
    s = "[Vid Request: mac={0}, vid={1}  port={2}]".format(self.mac, self.ip, self.port)
    if isinstance(self.next, packet_base):
      return s + str(self.next)    
    return s

  def parse(self, raw):
    assert isinstance(raw, bytes)
    self.raw = raw
    dlen = len(raw)
    if dlen < vid_request.MIN_LEN:
      self.msg('(local_host) warning local_host packet data too short to parse header: data len %u' % (dlen,))
      return

    
   
    mac = raw[:6]
    hdr = struct.unpack("!II", raw[6:vid_request.MIN_LEN])    
   
    self.mac = EthAddr(mac)
    self.ip =  IPAddr(hdr[0])
    self.port = hdr[1]
   
    self.parsed = True    
    

  def hdr(self, payload):
    buf =  self.mac.raw + self.ip.raw + struct.pack("!I", self.port)

    return buf
