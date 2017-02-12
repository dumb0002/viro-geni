from pox.core import core
from viro.packet.vid import VidAddr
from viro.packet.viro_ctrl import viroctrl
import time
from bucket import *
from routing_table import RoutingTable
from rdv_store import *
import collections as cl

log = core.getLogger()

class ViroRouting(object):
  
  # Time interval to discover neighbors failures
  # i.e. if we didn't hear from a neighbor for ALER_FAILURE
  # seconds, then we assume this neighbor has failed
  ALERT_FAILURE = 15
  
  def __init__(self, dpid, vid):
        self.dpid = dpid
        self.vid = vid
        self.L = VidAddr.L
        self.routingTable = RoutingTable(vid, dpid)
        self.rdvStore = RdvStore()
        self.liveNbrs = {}
        self.portNbrs = {} # mapping of Nbrs = port #
        self.rdvRequestTracker = cl.defaultdict(dict)
    
      
  def discoveryEchoReplyReceived(self, nbrVid, port):
    """ Process a discoveryEchoReply form a direct neighbor """
    dist = nbrVid.delta(self.vid)
                 
    bucket = Bucket(dist, nbrVid, self.vid, port)
    self.routingTable.addBucket(bucket)
    
    self.liveNbrs[nbrVid] = time.time()
    self.portNbrs[port] = nbrVid
    
    log.debug(str(self.routingTable))
    log.debug(str(self.rdvStore))    

    
  def removeFailedNode(self, vid):
    """ Remove failed neighbor from routing table
    All entries in which "vid" is a nexthop or gateway node must be removed """
    log.debug("Removing failed neighbor {}".format(vid))
    
    buckets = {}
    if vid in self.routingTable.nbrs:
      buckets.update(self.routingTable.nbrs[vid])
    
    if vid in self.routingTable.gtws:
      buckets.update(self.routingTable.gtws[vid])    
    
    for bkt in buckets:
      self.routingTable.removeBucket(bkt)
    
    if vid in self.liveNbrs:    
      del self.liveNbrs[vid]
    

  def getNextHop(self, dst, op=None):
    """ Find the nexthop node for the give dst """        
    nexthop = None
    port = None
        
    while not nexthop: 
      level = self.vid.delta(dst)
      if level == 0:
        return (nexthop, port)
      
      if level in self.routingTable:
        buckets = self.routingTable[level]
        if len(buckets) > 0 :
          bkt = buckets.iterkeys().next()
          return (bkt.nexthop, bkt.port)
      
      if (op != viroctrl.RDV_PUBLISH) and (op != viroctrl.RDV_QUERY):
        return (nexthop, port)
      
      # flip the 'level' bit to get closer
      dst = dst.flipBit(level)
        
  def selfRVDQuery(self, svid, k):  
    # search in rdv store for the logically closest gateway to reach kth distance away neighbor
    gw = self.rdvStore.findAGW(k, svid)
  
    # if found then form the reply packet and send to svid
    if not gw: # No gateway found
        log.debug('Node : {} has no gateway for the rdv_query packet to reach bucket: {}  for node: '.format(str(self.vid), k, str(svid)))
        return
    
    if k in self.routingTable:
      log.debug('Node {} has already have an entry to reach neighbors at distance - {}'.format(svid, k))
      return
  
    nexthop, port = self.getNextHop(gw)
    if not nexthop:
      log.debug('No nexthop found for the gateway: {}'.format(str(gw)))
      return
    
    # Destination Subtree-k
    bucket = Bucket(k, nexthop, gw, port)
    self.routingTable.addBucket(bucket)

  
  
  def rdvWithDraw(self, svid, failedGw):            
    log.debug('Node : {} has received rdv_withdraw from {}'.format(str(self.vid), str(svid)))
  
    #levels = self.rdvStore.findLevelsForGateway(failedGw)
  
    self.rdvStore.deleteGateway(failedGw)
    
    if self.vid != svid: # I am the rvd itself: no need to update routing table.
        self.removeFailedNode(failedGw)  # update the Routing Table
    else:
      log.debug("I am the rdv point. My routing table is already updated.")
    
    #return  levels
  

    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
     
