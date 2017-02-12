import itertools as it

class Bucket(object):
  """ A wrapper for a bucket entry in the routing table """
    
  def __init__(self, k, nexthop, gateway, port, default=False):
    """ Initialize the bucket entry variables """          
    # nexthop and gateway should be a VidAddr instance
    self.nexthop = nexthop
    self.gateway = gateway
    self.port = port
    self.k = k
    self.default = default
    
    self._hashval = "{}:{}:{}".format(k, nexthop.sw, gateway.sw).__hash__()
        
  def is_default(self):
    return self.default
  
  def __hash__(self):
    return self._hashval
  
  @property
  def key(self):
    return self._hashval
  
  def __eq__(self, other):
    if self.nexthop != other.nexthop: return False
    if self.gateway != other.gateway: return False
    if self.k != other.k: return False
    return True
          
  def __str__(self):
    s = 'Bucket(Level {} Nexthop {} Gateway {} Port {} Default {})'.format(
      self.k, self.nexthop.to_bin(), self.gateway.to_bin(), self.port, self.default)
    return s
  
  