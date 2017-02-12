import struct
import itertools as it

class VidAddr(object):
  
  # length of the switch part in the vid (4-bytes)
  # which is used for routing computations
  L = 32
  
  # The string conversion of the switch (4-bytes) into
  # a binary string format
  binFormat = "{0:0%db}" % (L)
  
  def __init__(self, sw, host):
    """ Initialize vid object
    Both sw and host are integers in host byte-order """
    self.sw = sw  
    self.host = host
    self.bin_str = VidAddr.binFormat.format(sw)
    self._value = (((sw & 0xffffffff) << 16) | host)
    
  def __eq__(self, other):
    if self.sw != other.sw: return False
    if self.host != other.host: return False
    return True
  
  def delta(self, vid):
    """ Computes the logical distance between self and vid """
    v1 = self.to_bin()
    v2 = vid.to_bin()
    iter = it.dropwhile(lambda p: p[0] == p[1], it.izip(v1, v2))
    dist = sum(1 for i in iter)
    return dist
  
  def getRendezvousID(self, level):
    """ Compute the RDV point VID for the given level """
    rdv = self.bin_str[:VidAddr.L-level+1]
    rdv = "{}{}".format(rdv, VidAddr.hashval(rdv, level-1))
    rdv = VidAddr(int(rdv, 2), 0)
    return rdv
  
  def flipBit(self, k):
    """ flips the kth bit (from the right) in the vid and returns it """   
    L = VidAddr.L
    b = self.bin_str
    
    bit = '1' if b[L-k] == '0' else '0' 
    vid = "{}{}{}".format(b[:L-k], bit, b[L-k+1:])
    vid = VidAddr(int(vid, 2), 0)
    
    return vid
    
  
  def __len__(self):
    return 6
  
  def to_raw(self):
    return struct.pack("!IH", self.sw, self.host)
  
  @property
  def raw(self):
    return self.to_raw()
  
  def to_bin(self):
    """ Convert the Vid to binary string 
    Note that we only convert the sw 4-bytes without the host 2-bytes """
    return self.bin_str
    
  
  def __str__(self):
    return '%#04x:%#04hx' % (self.sw, self.host)
  
  def __hash__(self):
    return self._value.__hash__()
  
  def __setattr__(self, attr, value):
    if hasattr(self, '_value'):
      raise TypeError("Modifying immutable object")
    object.__setattr__(self, attr, value)
    
  
  def bucketPrefix(self, k):
    """ Compute the routing prefix string for the given vid and level k """
    bit = '1' if self.bin_str[VidAddr.L-k] == '0' else '0'        
    prefix = self.bin_str[:VidAddr.L-k] + bit
    suffix = '*' * (k-1)
    return prefix + suffix
  
  @staticmethod
  def hashval(bin_str, length):
    return length*'0'      
    

  def getSWHost(self, Bytes):
     # given a 6 bytes array
     # returns the 4 bytes sw and 2 bytes as an integer
     sw = 0
     host = 0
     sw += ord(Bytes[0])*256**3
     sw += ord(Bytes[1])*256**2
     sw += ord(Bytes[2])*256
     sw += ord(Bytes[3])
     host += ord(Bytes[4])*256
     host += ord(Bytes[5])

     return (sw, host)
