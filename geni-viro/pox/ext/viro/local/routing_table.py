import itertools as it
import time

from pox.core import core
from viro.packet.vid import VidAddr
from bucket import *

log = core.getLogger()

class RoutingTable(object):
  """ A routing table is a dictionary of levels, where each level is
  a BucketList. A BucketList stores buckets for a level 'k' in the routing table """
  
  def __init__(self, vid, dpid):
    self.vid = vid
    self.dpid = dpid
    self.L = VidAddr.L
    
    # routing table dictionary
    self.rtbl = {}
    # all buckets
    self.bkts = {}
    # all neighbors "nexthops"
    self.nbrs = {}
    # all gateway nodes
    self.gtws = {}
    
    # track the bkts hash value already seen (added) to avoid addidng duplicated bkts
    self.bkts_hash = {}
    
    
  def addBucket(self, bucket):
    """ Add a bucket to the routing table """
    level = bucket.k
    nh = bucket.nexthop
    gw = bucket.gateway
    bkt_key = bucket.key

    if not bkt_key in self.bkts_hash:
        # add the level if it is not in the routing table, then add the bucket
        self[level] = self[level] if level in self else {}    
        self[level][bucket] = True
    
        # add the bucket to the list of all buckets
        self.bkts[bucket] = True

        # add the nexthop node the the list of neighbors
        self.nbrs[nh] = self.nbrs[nh] if nh in self.nbrs else {}
        self.nbrs[nh][bucket] = True
    
        # add the gateway node to the list of gateways
        self.gtws[gw] = self.gtws[gw] if gw in self.gtws else {}
        self.gtws[gw][bucket] = True

        
        self.bkts_hash[bkt_key] = True
    
  
  def removeBucket(self, bucket):
    """ Delete the bucket from the routing table """
    level = bucket.k
    nh = bucket.nexthop
    gw = bucket.gateway
    bkt_key = bucket.key
    
    # remove the bucket from the level and delete the level if empty
    del self[level][bucket]
    if not self[level]:
      del self[level]
    
    # remote the bucket from the list of all buckets
    del self.bkts[bucket]
    
    # remote the nexthop form the list of neighbors for this bucket
    del self.nbrs[nh][bucket]
    if not self.nbrs[nh]:
      del self.nbrs[nh]
    
    # remote the gateway node from the list of gateways for this bucket
    del self.gtws[gw][bucket]
    if not self.gtws[gw]:
      del self.gtws[gw]

    # remove the bkt hash key from the bkts hash value list 
    del self.bkts_hash[bkt_key]
  

  def removeAllBucketsInLevel(self, level):

    for bucket in self[level]:
      # remove nexthop from the list of neighbors
      del self.nbrs[bucket.nexthop][bucket]

      if not self.nbrs[bucket.nexthop]:
        del self.nbrs[bucket.nexthop]

      # remove gateway node from the list of gateways
      del self.gtws[bucket.gateway][bucket]

      if not self.gtws[bucket.gateway]:
        del self.gtws[bucket.gateway]

      # remove the bkt hash key
      del self.bkts_hash[bucket.key]

      # remote the bucket from the list of all buckets
      del self.bkts[bucket]
    
    # remove the level itself.
    del self[level]
    

  def findBucketsForNexthop(self, nexthop):
    vals = {}
    if nexthop in self.nbrs:
      vals.update(self.nbrs[nexthop])
    return vals
  
  def findBucketsForGateway(self, gateway):
    vals = {}
    if gateway in self.gtws:
      vals.update(self.gtws[gateway])
    return vals
  
  def __getitem__(self, level):
    return self.rtbl[level]
  
  def __delitem__(self, level):
    del self.rtbl[level]
  
  def __setitem__(self, level, blist):
    self.rtbl[level] = blist
  
  def __contains__(self, level):
    return level in self.rtbl
  
  def __hash__(self):
    self.rtbl.__hash__()
  
  def __eq__(self, other):
    return (self.rtbl == other.rtbl)
  
  def __str__(self):
    """ Convert the routing table into a readable string for debugging """
    s = '\n----> Routing Table at : {} | {} <----\n'.format(self.vid.sw, self.dpid)
    
    for level in range(1, self.L+1):
      if level in self:
        l = ', '.join(it.imap(lambda b: str(b), self[level].iterkeys()))
        prefix = self.vid.bucketPrefix(level)
        s += 'Level:: {} Prefix {} BucketList[{}]\n'.format(level, prefix, l)
      else:
           
        s += 'Level:: {} {}\n'.format(level, '----- EMPTY -----')
    s += '\n --  --  --  --  -- --  --  --  --  -- --  --  --  --  -- \n'
    
    return s
  
  def __len__(self):
    return len(self.rtbl)
  
  def __iter__(self):
    return self.rtbl
  
  def next(self):
    return self.rtbl.next()
    
    
