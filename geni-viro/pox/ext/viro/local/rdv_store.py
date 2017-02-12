import itertools as it
import time

from pox.core import core
from viro.packet.vid import VidAddr

log = core.getLogger()


class RdvPoint(object):
  def __init__(self, gateway, nexthop):
    self.gw = gateway
    self.nh = nexthop
    self._hashval = "{}:{}".format(gateway.sw, nexthop.sw).__hash__()
  
  def __hash__(self):
    return self._hashval
  
  @property
  def key(self):
    return self._hashval

  def __eq__(self, other):
    if self.gw != other.gw: return False
    if self.nh!= other.nh: return False
    return True


  
class RdvStore(object):
  
  def __init__(self):
    self.store = {}
    
    
  def addRdvPoint(self, k, gateway, nexthop):
    if k not in self.store:
      self.store[k] = {}
      
    p = RdvPoint(gateway, nexthop)
    key = p.key
    self.store[k][key] = p
      
  
  def findLevelsForGateway(self, gw):
    levels = {}
    
    for k in self.store:
      for rdv in self.store[k]:
        if self.store[k][rdv].gw == gw:
          levels[k] = True
          
    return levels
  

  def deleteGatewayPerNextHop(self, gw, nh):
    
    for k in self.store:
      for rdv in self.store[k]:
        if self.store[k][rdv].gw == gw and self.store[k][rdv].nh == nh:
           del self.store[k][rdv]
           return 

  def deleteGateway(self, gw):
    entries = []
    
    for k in self.store:
      for rdv in self.store[k]:
        if self.store[k][rdv].gw == gw:
          entries.append((k, rdv))
          
    for k, rdv in entries:
      del self.store[k][rdv]
  
      
  def findAGW(self, k, svid):    
    gw = {}
    
    if k not in self.store:
       return None
     
    for t in self.store[k]:
      t = self.store[k][t]
      r = svid.delta(t.gw)
      # FIXME add support for multipath routing
      gw[r] = t.gw
    
    if len(gw) == 0:
       return None
    
    closest_level = sorted(gw.keys())[0]
    return gw[closest_level]

  
  def findNextHop(self, gw, k):
      nexthop = None

      for rdv in self.store[k]:
        if self.store[k][rdv].gw == gw:
          nexthop = self.store[k][rdv].nh
          
      return nexthop



  def findGWByNextHop(self, nh):
      entries = []
    
      for k in self.store:
        for rdv in self.store[k]:
          if self.store[k][rdv].nh == nh:
            entries.append(self.store[k][rdv].gw)
      return entries


  
  def __str__(self):
    """ Convert the RDV table into a readable string for debugging """
    s = 'RDV STORE: '

    if len(self.store) > 0:
      for level in self.store:
         
         if len(self.store[level]) > 0:
           s += '[Level:: {}'.format(level)

           for t in self.store[level]:
           
             t = self.store[level][t]
             gw = t.gw
             nexthop = t.nh                                  
             s += '  Gateway:: {} NextHop:: {}'.format(gw, nexthop)
           s += ']'

         else: 
           s += '[----- EMPTY -----]\n'
    else:
        s += '[----- EMPTY -----]\n'
    s += '\n----------------------------------------------------------\n'
    return s

    
  
  
