import time
from pox.core import core
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.util import str_to_bool
from pox.lib.recoco import Timer
import pox.lib.packet as pkt

import viro.factory.message as msgFactory
import viro.factory.packet as pktFactory
from viro.switch import Switch

from viro.packet.viro_ctrl import viroctrl
from viro.packet.viro import viro
from viro_routing import ViroRouting
from viro.packet.vid import VidAddr
from rdv_store import *
from routing_table import *
from bucket import *
from viro.topology import Topology

import pox.openflow.nicira as nx
import pox.openflow.libopenflow_01 as of

import copy
from routing_table import RoutingTable

import logging
import datetime



log = core.getLogger()



class LocalViro(EventMixin):
  """
  Waits for OpenFlow switches to connect and makes them viro switches.
  This module is supposed to be the management plane for viro
  """

  _core_name = "viro_local"

  CONTROLLER_ID = 2
  RemoteViro_CONTROLLER_ID = 1
  
  # ROUND_TIME this is the waiting time for each round in number of seconds
  ROUND_TIME = 5

  # NEIGHBOUR DISCOVERY wait time
  DISCOVER_TIME = 5

  # Wait time for populating routing table
  UPDATE_RT_TIME = 10

  # Failure time interval
  FAILURE_TIME = 7 

  # temporary variable (used to push routing table)
  counter = 0
  
  # Nov.2015 Count of control packets
  numOfVIRO = 0
  numOfVIRO_CONTROLLER_ECHO = 0
  numOfVIRO_LOCAL_HOST = 0
  numOfVIRO_DISC_ECHO_REQ = 0
  numOfVIRO_DISC_ECHO_REPLY = 0
  numOfVIRO_DISC_ECHO_REPLY_SENT = 0  
  numOfVIRO_RDV_PUBLISH = 0
  numOfVIRO_RDV_QUERY = 0
  numOfVIRO_RDV_REPLY = 0
  numOfVIRO_RDV_REPLY_SENT = 0  
  numOfVIRO_RDV_WITHDRAW = 0
  numOfVIRO_RDV_WITHDRAW_SENT = 0
  numOfVIRO_GW_WITHDRAW = 0
  numOfVIRO_GW_WITHDRAW_SENT = 0


  def __init__(self):
    self.listenTo(core.viro_core)
    self.sw = Switch(None, None, None)
    self.routing = ViroRouting(None, None)
    self.L = VidAddr.L
    self.local_topo = Topology()

  def _handle_ViroSwitchUp(self, event):
    """ Local VIRO switch is connecting to the local controller
    We set the controller Id to our local VIRO controller """
    log.debug("Connection %s %s" % (event.connection, dpidToStr(event.dpid)))

    self.sw.dpid = event.dpid
    self.sw.connection = event.connection
    
    self.routing.dpid = event.dpid
    self.routing.routingTable.dpid = event.dpid

    # Guobao added 02/05/2015
    #self.previousRoutingTable = copy.deepcopy(self.routing.routingTable)
    self.previousRoutingTable = RoutingTable(None, None)

    # Turn on ability to specify table in flow_mods
    msg = nx.nx_flow_mod_table_id()
    self.sw.connection.send(msg)
    
    msg = msgFactory.ofpControllerId(LocalViro.CONTROLLER_ID)
    self.sw.connection.send(msg)
    
    
    msg = msgFactory.ctrlPktsLocalViroPacketIn(LocalViro.CONTROLLER_ID)  # set the rule for Viro Packets
    self.sw.connection.send(msg)


    msg_ip = msgFactory.IPv4LocalViroPacketIn(LocalViro.CONTROLLER_ID)   # set the rule for IP Packets
    self.sw.connection.send(msg_ip)

    # Guobao -- Fallback rule for Table 0
    msg = msgFactory.FallBack(1)
    self.sw.connection.send(msg)

    # Start periodic function of the local controller
    # 1. Neighbor discovery
    # 2. Routing table rounds
    # 3. Failure discovery
    # We don't use recurring timers to avoid function call overlaps in case of delays
    # So, we call the timer function after the end of the callback function
    Timer(LocalViro.DISCOVER_TIME, self.neibghoorDiscoverCallback)
    #Timer(LocalViro.FAILURE_TIME, self.discoveryFailureCallback) # comment here
    
    self.round = 1
    Timer(LocalViro.UPDATE_RT_TIME, self.startRoundCallback)
    
    # Sync RT Table every UPDATE_RT_TIME?
    Timer(LocalViro.UPDATE_RT_TIME, self.pushRTHelper)


  def _handle_ViroSwitchPortStatus(self, event):
       #Handle switch modified port status
       # check if the modified port is connected to a host or switch
       # if a) "host": remove the specific host from its topology table
       # notifies the remote controller that the host was removed 
       # from the switch topology; b) "switch": initiates VIRO failure recovery mechanism

       log.debug("Receiving a port status event")

       ofp = event.ofp

       if ofp.reason == of.OFPPR_MODIFY:
          port = ofp.desc.port_no # modified or deleted port number
          known_host = self.local_topo.findHostByPort(port)

          if not known_host == None:
             
             log.debug("Updating its local topology: local host was disconnected")
             ip = known_host.ip
             self.local_topo.deleteHostByIP(ip) # remove host
              
             # sends a notification to remote controller
             # sending host withdraw message to remote controller
             packet = pktFactory.hostWithdraw(ip)
             msg = msgFactory.controllerEcho(LocalViro.RemoteViro_CONTROLLER_ID, packet)
             self.sw.connection.send(msg)
  
             return

          else: 
             # the removed port is connected to a switch
             log.debug("Discovered neibghor failed: starting VIRO failure recovery mechanism")
             self.discoveryFailure(port)  #uncomment here                               


  def _handle_ViroPacketInIP(self, event):

      IPv4_frame = event.packet
      inport = event.port
      IPv4pkt = IPv4_frame.payload   # Ip packet payload

      log.debug("IPv4 packet in_port=%d, srcvid=%s, dstvid=%s, type=%#04x",
             inport, IPv4_frame.src, IPv4_frame.dst, IPv4_frame.type,)

   
      # Is it to us? (eg. not a DHCP packet)
      if isinstance(IPv4pkt, pkt.dhcp):
        log.debug("%s: packet is a DHCP: it is not for us", str(event.connection))
        return


      # obtain the frame header info.
      srcMac = IPv4_frame.src
      dstMac = IPv4_frame.dst
      ethtype =  IPv4_frame.type
      ipv4 = IPv4pkt.srcip
 
      log.debug("This is the ipv4 packet: {}".format(ipv4))


      n = dstMac.toRaw() 
      dst_sw, dst_host = self.sw.vid.getSWHost(n)
      dst_vid = VidAddr(dst_sw, dst_host)

      # find src and dst host objects
      #dist_host = self.local_topo.findHostByVid(dst_vid)
      dist_host = self.local_topo.findHostByMac(dstMac)
      local_host = self.local_topo.findHostByMac(srcMac)


      # if local host does not exist in our topology 
      # send a vid request to the remote controller
      # Drop the IPv4 pkts
      if local_host == None:
          packet = pktFactory.vidRequest(srcMac, ipv4, inport)
          msg = msgFactory.controllerEcho(LocalViro.RemoteViro_CONTROLLER_ID, packet)
          self.sw.connection.send(msg)

          log.debug("Sending a Vid Request pkt to the remote controller")
          return 

      # obtain the src VidAddress
      src_vid = local_host.vid
          

      if dist_host != None:
          ###### Handling packets to src and dst in the same switch ######
          log.debug("src and dst attached to the same switch!")
        
          lport = dist_host.port
          #dst_mac = dist_host.mac
          #etherpkt = event.packet
        
          # set the destination macAddress and the source vid
          #etherpkt.src = src_vid.to_raw()
          #etherpkt.dst = dst_mac

          
          log.debug("forwarding the packet to the next host")
          msg =  msgFactory.packetOut(IPv4_frame, lport)
          self.sw.connection.send(msg)

          #---------------------------------------------        
             # Add a rule to the switch for future packets
          #---------------------------------------------
          log.debug("pushing the rules to the switch")
          #msg = msgFactory.rewriteMac(src_vid, dstMac, dst_mac, lport)

          # Pushing the rule in both directons
          # a) src --> dst
          msg = msgFactory.rewriteMac(srcMac, dstMac, lport)
          self.sw.connection.send(msg)

          # b) dst --> src
          msg = msgFactory.rewriteMac(dstMac, srcMac, inport)
          self.sw.connection.send(msg)

          return 

      else:

          ###### Handling packets to src and dst in different switch ######
          log.debug("Converting IPv4pkts to Viropkts")
         

          # Generates a Viropkt frame and route it
          log.debug('VidAddress parameters - Src: {} , Dst: {}'.format(src_vid, dst_vid))  

          viropkt = pktFactory.ViroPacket(src_vid, dst_vid, None, ethtype, IPv4pkt)
          self.routeViroPacket(viropkt, True)
      
          log.debug("routing Viro packets")

          #---------------------------------------------        
             # Add a rule to the switch for future packets
          #---------------------------------------------
          # log.debug("Port is {}".format(outport))
          msg = msgFactory.encapsulate(srcMac, src_vid, dstMac, dst_vid)
          self.sw.connection.send(msg)
      
          return



  def _handle_ViroPacketInVIROData(self, event):
    """ VIRO data packet received """
    
    # FIXME we need to add code to handle data packet missed by the routing
    # table inside the switch. This can happend due to inconsistency between
    # the controller routing table and the switch routing table    
    viropkt = event.packet
    inport = event.port
    
    log.debug("PacketInVIROData in_port=%d, srcvid=%s, dstvid=%s, type=%#04x, fd=%s, eth_type=%#04x",
              inport, viropkt.src, viropkt.dst, viropkt.type, viropkt.fd, viropkt.effective_ethertype)
        
    self.processDataPacket(viropkt, inport)

  def _handle_ViroPacketInVIROCtrl(self, event):
    """ VIRO control packet received """
    
    viropkt = event.packet
    inport = event.port
    
    log.debug(str(viropkt))
    
    ctrlpkt = viropkt.payload
    
    if ctrlpkt.op == viroctrl.CONTROLLER_ECHO:
      self.numOfVIRO_CONTROLLER_ECHO = self.numOfVIRO_CONTROLLER_ECHO + 1
      logging.info("VIRO_CONTROLLER_ECHO " + str(self.numOfVIRO_CONTROLLER_ECHO) + " " + str(time.time()) + " R")

      # remote controller echo message received, which is used to receive
      # the vid of the local switch from the remote controller
      echo = ctrlpkt.payload
      self.sw.vid = echo.vid
      self.routing.vid = echo.vid
      self.routing.routingTable.vid = echo.vid

      return

    if ctrlpkt.op == viroctrl.LOCAL_HOST:
       self.numOfVIRO_LOCAL_HOST = self.numOfVIRO_LOCAL_HOST + 1
       logging.info("VIRO_LOCAL_HOST " + str(self.numOfVIRO_LOCAL_HOST) + " " + str(time.time()) + " R")

       # remote controller host message, which contains
       # It contains the mac,vid,ip of the host attached to this local controller
       log.debug('Receiving local host information from remote controller')
       payload = ctrlpkt.payload
       host  = payload.host
       host.sw = self.sw.vid
       self.local_topo.addHost(host)
       
       return        

          
    if not self.sw.vid:
      # if we didn't receive the switch vid from the remote controller yet
      # we return immediately since this means that we don't know our vid yet
      return

    self.processCtrlPacket(viropkt, inport)
  
  def processViroPacket(self, viropkt, inport):
    """ Porcess a locally generated viro packet """
    if viropkt.effective_ethertype == viroctrl.VIRO_CTRL_TYPE:
      self.processCtrlPacket(viropkt, inport)
    else:
      self.processDataPacket(viropkt, inport)
  
  def processDataPacket(self, viropkt, inport):
    """ Process a VIRO data packet """
    # 1.proces the packet
    # 2. Add a rule to the switch to match future requests
    # 3. Need to check if I am the destination of the packet
    # If so remove the forwarding directive, replace the 
    # Vid with the mac address with the client mac address and forward 
    # the packet to the host: I need to save to which port the client is 
    # connected to

    dst = viropkt.dst
    src = viropkt.src    
    dst_pkt = VidAddr(dst.sw, 0x00)

    
    if dst_pkt == self.sw.vid:
         
        # I am the destination for the packet:
        # converting a Viropkt frame to ethernet frame


        log.debug("Destination VID: {}   myVid: {}".format(dst, self.sw.vid)) 
        datapkt = viropkt.payload
        local_host = self.local_topo.findHostByVid(dst)

        if local_host == None:
           log.debug("Unknown destination Vid to hosts attached to this switch!")
           return 

        srcMac = src.to_raw()
        dstMac = local_host.mac
        lport = local_host.port
        type = viropkt.effective_ethertype
        
        # Generates a internet frame and route it
        etherpkt = pktFactory.ethernetPkt(type, srcMac, dstMac, datapkt)
        msg =  msgFactory.packetOut(etherpkt, lport)
        self.sw.connection.send(msg)

        log.debug("Sending data packets to local hosts")


        #---------------------------------------------        
        # Add a rule to the switch for future packets
        #---------------------------------------------
        msg = msgFactory.decapsulate(dstMac, dst, lport)
        self.sw.connection.send(msg)

        return 

    else:
         
        # Viropkt is not for us then route it!
        port = self.routeViroPacket(viropkt)

        #---------------------------------------------        
        # Add a rule to the switch for future packets
        #---------------------------------------------
        level = self.sw.vid.delta(dst_pkt)
        prefix = self.sw.vid.bucketPrefix(level)
        dst_vid = int(prefix.replace("*","0"), 2)
        dst_vid_mask = int(prefix.replace("0","1").replace("*","0"), 2)

        msg = msgFactory.pushRoutingTable(dst_vid, dst_vid_mask, port)
        self.sw.connection.send(msg)

        msg = msgFactory.pushRoutingTableETH(dst_vid, dst_vid_mask, port)
        self.sw.connection.send(msg)

        return 

    #raise Exception("processDataPacket not implemented yet")
      
  def processCtrlPacket(self, viropkt, inport):
    """ Comsume a viro control packet """
    ctrlpkt = viropkt.payload
    
    if ctrlpkt.op == viroctrl.DISC_ECHO_REQ:
      self.numOfVIRO_DISC_ECHO_REQ = self.numOfVIRO_DISC_ECHO_REQ + 1
      logging.info("VIRO_DISC_ECHO_REQ " + str(self.numOfVIRO_DISC_ECHO_REQ) + " " + str(time.time()) + " R")

      echo = ctrlpkt.payload
      nvid = viropkt.src
      
      reply = pktFactory.discoverEchoReply(self.sw.vid, nvid)
      self.numOfVIRO_DISC_ECHO_REPLY_SENT = self.numOfVIRO_DISC_ECHO_REPLY_SENT + 1
      logging.info("VIRO_DISC_ECHO_REPLY " + str(self.numOfVIRO_DISC_ECHO_REPLY_SENT) + " " + str(time.time()) + " S")
      msg =  msgFactory.packetOut(reply, inport)
      
      self.sw.connection.send(msg)
      log.debug("Neighbor discovery reply sent")
      
      return

    elif ctrlpkt.op == viroctrl.DISC_ECHO_REPLY:
      self.numOfVIRO_DISC_ECHO_REPLY = self.numOfVIRO_DISC_ECHO_REPLY + 1
      logging.info("VIRO_DISC_ECHO_REPLY " + str(self.numOfVIRO_DISC_ECHO_REPLY) + " " + str(time.time()) + " R")

      nvid = viropkt.src    
      self.routing.discoveryEchoReplyReceived(nvid, inport)

      return

    if not viropkt.dst == self.sw.vid:
      # forward the control packet since its not for me
      self.routeViroPacket(viropkt)
      return   
    
    # handle viro routing packets i.e. publish, query, etc.
    if ctrlpkt.op == viroctrl.RDV_PUBLISH:
      self.numOfVIRO_RDV_PUBLISH = self.numOfVIRO_RDV_PUBLISH + 1
      logging.info("VIRO_RDV_PUBLISH " + str(self.numOfVIRO_RDV_PUBLISH) + " " + str(time.time()) + " R")

      nexthop = ctrlpkt.payload.vid      
      svid = viropkt.src        
      log.debug("RDV_PUBLISH message received from: ".format(str(svid)))
  
      dist = self.sw.vid.delta(nexthop)      
      self.routing.rdvStore.addRdvPoint(dist, svid, nexthop)
    
    elif ctrlpkt.op == viroctrl.RDV_QUERY:
      self.numOfVIRO_RDV_QUERY = self.numOfVIRO_RDV_QUERY + 1
      logging.info("VIRO_RDV_QUERY " + str(self.numOfVIRO_RDV_QUERY) + " " + str(time.time()) + " R")

      log.debug("RDV_QUERY message received")
      src = viropkt.src
      if src == self.sw.vid:
        log.debug("I am the rdv point - processing the packet")
        self.routing.selfRVDQuery(src, ctrlpkt.payload.bucket_dist)
      else:
        svid = viropkt.src
        k = ctrlpkt.payload.bucket_dist
        log.debug("RDV_QUERY message received from: {}".format(svid))
  
        # search in rdv store for the logically closest gateway to reach kth distance away neighbor
        gw = self.routing.rdvStore.findAGW(k,svid)
  
        # if found then form the reply packet and send to svid
        if not gw:
            # No gateway found
            log.debug('Node : {} has no gateway for the rdv_query packet to reach bucket: {} for node: {}'.format(self.sw.vid, k, svid))
            return
  
        # create a RDV_REPLY packet and send it        
        rvdReplyPacket = pktFactory.rdvReply(self.sw.vid, svid, k, gw) 
  
        # Keeps track of the Nodes that requests each Gateways at specific level
        nh = self.routing.rdvStore.findNextHop(gw,k) # nexthop associated with the selected gateway
        self.routing.rdvRequestTracker[gw][svid] = nh

        self.numOfVIRO_RDV_REPLY_SENT = self.numOfVIRO_RDV_REPLY_SENT + 1
        logging.info("VIRO_RDV_REPLY " + str(self.numOfVIRO_RDV_REPLY_SENT) + " " + str(time.time()) + " S")
    
        msg = msgFactory.packetOut(rvdReplyPacket, inport) 
        self.sw.connection.send(msg)
        log.debug("RDV_REPLY message sent")       
      
    elif ctrlpkt.op == viroctrl.RDV_REPLY:
      self.numOfVIRO_RDV_REPLY = self.numOfVIRO_RDV_REPLY + 1
      logging.info("VIRO_RDV_REPLY " + str(self.numOfVIRO_RDV_REPLY) + " " + str(time.time()) + " R")

      log.debug("RDV_REPLY message received") 
      # Fill my routing table using this new information
      rtbl = self.routing.routingTable
      gw = ctrlpkt.payload.gw
      k = ctrlpkt.payload.bucket_dist
        
      if k in self.routing.routingTable:
        log.debug('Node {} has already have an entry to reach neighbors at distance - {}'.format(self.sw.vid, k))
        return
  
      dist = self.sw.vid.delta(gw)
      if dist not in rtbl:
        log.debug('ERROR: no nexthop found for the gateway: {}'.format(str(gw)))
        return
        
      bucket = rtbl[dist].iterkeys().next()
      nexthop = bucket.nexthop
      port = bucket.port      

      bucket = Bucket(k, nexthop, gw, port)    
      rtbl.addBucket(bucket)

    elif ctrlpkt.op == viroctrl.RDV_WITHDRAW:
      self.numOfVIRO_RDV_WITHDRAW = self.numOfVIRO_RDV_WITHDRAW + 1
      logging.info("VIRO_RDV_WITHDRAW " + str(self.numOfVIRO_RDV_WITHDRAW) + " " + str(time.time()) + " R")

      #log.debug('RDV_WITHDRAW message received from: {}'.format())
      svid = viropkt.src
      gw = ctrlpkt.payload.gw
      k = ctrlpkt.payload.bucket_dist
      
      log.debug('RDV_WITHDRAW message received from: {} for gateway: {}'.format(svid, gw))
      self.routing.rdvWithDraw(svid, gw)
     
      # Sends Remove Gateway messages to the appropriated nodes
      if gw in self.routing.rdvRequestTracker:
            for dst in self.routing.rdvRequestTracker[gw]:
              # Sends the GW_WITHDRAW message to nodes
              pkt = pktFactory.gatewayWithdraw(self.sw.vid, dst, gw)
              nexthop, port = self.routing.getNextHop(dst)            
             
              if nexthop:
                self.numOfVIRO_GW_WITHDRAW_SENT = self.numOfVIRO_GW_WITHDRAW_SENT + 1
                logging.info("VIRO_GW_WITHDRAW " + str(self.numOfVIRO_GW_WITHDRAW_SENT) + " " + str(time.time()) + " S")

                log.debug('Sending GW_WITHDRAW message received from: {} to destination: {}'.format(self.sw.vid, dst))
                self.routeViroPacket(pkt)
              else:
                log.debug("No next hop found!")
              
            # delete the failed gateway from the rdvRequestTracker - House Keeping
            del self.routing.rdvRequestTracker[gw]                
            log.debug('Removed the failed gateway: {} from rvd request-tracker'.format(gw))



      # Remove all the Gateways using the "failed node" as nexthop (Fixme! simply this code)
      gw_entries = self.routing.rdvStore.findGWByNextHop(gw) # list of gateways using "failed node" as its nexthop
 
      delete_entries = []

      for gw_other in gw_entries:
         for dst in self.routing.rdvRequestTracker[gw_other]:

           if  self.routing.rdvRequestTracker[gw_other][dst] == gw:
               # Sends the GW_WITHDRAW message to nodes
               pkt = pktFactory.gatewayWithdraw(self.sw.vid, dst, gw_other)
               nexthop, port = self.routing.getNextHop(dst)            
             
               if nexthop:
                  self.numOfVIRO_GW_WITHDRAW_SENT = self.numOfVIRO_GW_WITHDRAW_SENT + 1
                  logging.info("VIRO_GW_WITHDRAW " + str(self.numOfVIRO_GW_WITHDRAW_SENT) + " " + str(time.time()) + " S")

                  log.debug('Sending GW_WITHDRAW message received from: {} to destination: {}'.format(self.sw.vid, dst))
                  self.routeViroPacket(pkt)
               else:
                  log.debug("No next hop found!")

               delete_entries.append((gw_other, dst))
               
               # deleting entry from the RDVStore
               self.routing.rdvStore.deleteGatewayPerNextHop(gw_other,gw)
               log.debug('Removed the failed gateway entry: {} from RDVStore per level'.format(gw_other))


      # delete any remaining gateway using the failed nexthop - House Keeping
      self.routing.rdvStore.deleteGatewayForNextHop(gw)

      # delete the failed gateway entry from the rdvRequestTracker - House Keeping
      for gw_other, dst in delete_entries:
          del self.routing.rdvRequestTracker[gw_other][dst]  
             
          log.debug('Removed the failed gateway entry: {} from rvd request-tracker'.format(gw_other))




    elif ctrlpkt.op == viroctrl.GW_WITHDRAW:
      self.numOfVIRO_GW_WITHDRAW = self.numOfVIRO_GW_WITHDRAW + 1
      logging.info("VIRO_GW_WITHDRAW " + str(self.numOfVIRO_GW_WITHDRAW) + " " + str(time.time()) + " R")

      failed_gw = ctrlpkt.payload.failed_gw
      log.debug('Received Gateway Withdraw for node: {}'.format(failed_gw))
      self.routing.removeFailedNode(failed_gw)

      #---------------------------------------------        
      # Push New Routing Table
      #---------------------------------------------
      # self.pushRT()
          
  
  def neibghoorDiscoverCallback(self):
    """ Periodically send neighbor discovery to my neighbors """
    if not self.sw.vid:
      log.debug("Local controller didn't receive the switch VID yet from the remote controller!!")
      return
    
    try: 
      self.numOfVIRO_DISC_ECHO_REQ = self.numOfVIRO_DISC_ECHO_REQ + 1
      logging.info("VIRO_DISC_ECHO_REQ " + str(self.numOfVIRO_DISC_ECHO_REQ) + " " + str(time.time()) + " S")
     
      packet = pktFactory.discoverEchoRequest(self.sw.vid)            
      # FIXME do we really want to flood here?      
      msg =  msgFactory.flood(packet)
      self.sw.connection.send(msg)
      log.debug("Neighbor discovery packets sent to neighbors")
    except Exception as e:
      log.error("Unable to send discovery packets. Exception({})".format( e ))
    
    # register the callback again  
    Timer(LocalViro.DISCOVER_TIME, self.neibghoorDiscoverCallback)
      
  def discoveryFailureCallback(self):
    """ Periodically discover link failures
    First, we find failed neighbors i.e. nodes that we didn't receive any discoverEchoReply from in a while
    Second, we delete those neighbors and update the RDV points """
    log.debug("Starting discovering neighbor failures")

    delete = [] # list of nodes to be deleted
    for nbrVid, timestamp  in self.routing.liveNbrs.iteritems():
      now = time.time()
  
      if (now - timestamp) > ViroRouting.ALERT_FAILURE:
        log.debug("Failed neighbor detected {}".format(nbrVid))
        
        delete.append(nbrVid)
        for bkt in self.routing.routingTable.nbrs[nbrVid]:
          if bkt.gateway == self.sw.vid or bkt.gateway == nbrVid:
            # notify the failure to RDV points
            k = bkt.k  # level
            rdvVid = self.sw.vid.getRendezvousID(k)
            
            if not rdvVid == nbrVid: # if the rdvVid is not the failed node
              self.numOfVIRO_RDV_WITHDRAW_SENT = self.numOfVIRO_RDV_WITHDRAW_SENT + 1
              logging.info("VIRO_RDV_WITHDRAW " + str(self.numOfVIRO_RDV_WITHDRAW_SENT) + " " + str(time.time()) + " S")


              #pkt = pktFactory.rdvWithdraw(self.sw.vid, rdvVid, bkt.gateway)
              pkt = pktFactory.rdvWithdraw(self.sw.vid, rdvVid, k, nbrVid)
              self.routeViroPacket(pkt)
            else:
              log.debug("RDV destination is not reachable to notify failure of node :{}".format(str(nbrVid)))
    
    flag = False

    # remove the failed neighbor from the routing table 
    for nbrVid in delete:
      flag = True
      self.routing.removeFailedNode(nbrVid)            
    
    #---------------------------------------------        
    # Push New Routing Table
    #---------------------------------------------
    #if flag == True:
      #self.pushRT()

    # register the callback again
    Timer(LocalViro.FAILURE_TIME, self.discoveryFailureCallback)

  
  def discoveryFailure(self, port):
      """ First, we find failed neighbors i.e. nodes use Openflow portStatus events
      Second, we delete those neighbors and update the RDV points """
      log.debug("Neighbor failure discovered ")

      nbrVid = self.routing.portNbrs[port]

      log.debug("Neighbor {} failed at port {}".format(nbrVid, port))

      for bkt in self.routing.routingTable.nbrs[nbrVid]:
          if bkt.gateway == self.sw.vid or bkt.gateway == nbrVid:
            # notify the failure to RDV points
            k = bkt.k  # level
            rdvVid = self.sw.vid.getRendezvousID(k)
            
            if not rdvVid == nbrVid: # if the rdvVid is not the failed node
              self.numOfVIRO_RDV_WITHDRAW_SENT = self.numOfVIRO_RDV_WITHDRAW_SENT + 1
              logging.info("VIRO_RDV_WITHDRAW " + str(self.numOfVIRO_RDV_WITHDRAW_SENT) + " " + str(time.time()) + " S")


              #pkt = pktFactory.rdvWithdraw(self.sw.vid, rdvVid, bkt.gateway)
              pkt = pktFactory.rdvWithdraw(self.sw.vid, rdvVid, k, nbrVid)
              self.routeViroPacket(pkt)
            else:
              log.debug("RDV destination is not reachable to notify failure of node :{}".format(str(nbrVid)))
    
      # remove the failed neighbor from the routing table:
      self.routing.removeFailedNode(nbrVid)          



  def routeViroPacket(self, pkt, inport=None):
    """ Route the viro packet closer to destination """

    dst_pkt = VidAddr(pkt.dst.sw, 0x00)

    if (dst_pkt == self.sw.vid):
      # consume the packet since its sent to me
      self.processViroPacket(pkt, inport)      
      return 

    
    if pkt.effective_ethertype == viroctrl.VIRO_CTRL_TYPE:
       op = pkt.payload.op
       nexthop, port = self.routing.getNextHop(dst_pkt, op)
    else:
       nexthop, port = self.routing.getNextHop(dst_pkt)


    if nexthop != None:
      msg = msgFactory.packetOut(pkt, port)
      self.sw.connection.send(msg)
    else:
      log.debug("routeViroPacket nexthop not found")
  
    # use for handling data packets
    if inport:
       return port
  
  def startRoundCallback(self):
    log.debug("Starting round {}".format(self.round))
    self.runARound()
    self.round += 1
    
    #if self.round == self.L: # push the routing table after populating all the levels
       #log.debug("Starting pushing the routing table to the switch......")
       #self.pushRT() 

    if self.round > self.L:
       self.round = self.L

    log.debug(str(self.routing.routingTable)) # print Routing Table
    log.debug(str(self.routing.rdvStore)) # print RDV store
    # register the callback again
    Timer(LocalViro.UPDATE_RT_TIME, self.startRoundCallback)   

  def pushRTHelper(self):   	
    self.pushRT()
    Timer(LocalViro.UPDATE_RT_TIME, self.pushRTHelper)

    
  def pushRT(self):
    # push the local controller routing table to the switch

    for level in range(1, self.L+1):
      if level in self.routing.routingTable:

        prefix = self.sw.vid.bucketPrefix(level)
        dst_vid = int(prefix.replace("*","0"), 2)
        dst_vid_mask = int(prefix.replace("0","1").replace("*","0"), 2)

        # Fixme: improve this code for multipath
        # We use 1000 as "maximum infinity" here since the maximum level will be no larger than 32.
        closestDistance = 1000
        closestBucket = None
        for bucket in self.routing.routingTable[level]:
          distance = self.sw.vid.delta(bucket.gateway)
          if (distance < closestDistance):
            closestDistance = distance
            closestBucket = bucket
	      
        port = closestBucket.port
        bkt_key = closestBucket.key   
        bkt_dict = self.previousRoutingTable.bkts_hash

        if bkt_key in bkt_dict:
          log.debug("No routing table pushed. No changes happened.")
        else:
          log.debug("Pushing rule for level: {}  dst_vid: {}  dst_mask: {}".format(level, dst_vid, dst_vid_mask))
          # Guobao Nov.2015 Fixed duplicate pushes
          if level in self.previousRoutingTable:
            self.previousRoutingTable.removeAllBucketsInLevel(level)
            
          self.previousRoutingTable.addBucket(closestBucket)
          msg = msgFactory.pushRoutingTable(dst_vid, dst_vid_mask, port)
          self.sw.connection.send(msg)
          msg = msgFactory.pushRoutingTableETH(dst_vid, dst_vid_mask, port)
          self.sw.connection.send(msg)

      else:
        log.debug("Failure to push rule for level {} : -- EMPTY LEVEL --".format(level))


      
  def runARound(self):
    round = self.round
    rtbl = self.routing.routingTable
    myvid = self.sw.vid
        
    # start from round 2 since connectivity in round 1 is already learned using the physical neighbors
    for i in range(2, round+1):
      # see if routing entry for this round is already available in the routing table.
      if i in rtbl:
        if len(rtbl[i]) > 0:
          #publish the information if it is already there
          for bkt in rtbl[i]:
            if bkt.gateway == myvid:               
              log.debug("Sending rdv publish messages")

              self.numOfVIRO_RDV_PUBLISH = self.numOfVIRO_RDV_PUBLISH + 1
              logging.info("VIRO_RDV_PUBLISH " + str(self.numOfVIRO_RDV_PUBLISH) + " " + str(time.time()) + " S")

              dst = myvid.getRendezvousID(i)
              pkt = pktFactory.rdvPublish(myvid, dst, bkt.nexthop)              
              self.routeViroPacket(pkt)
              log.debug("RDV publish messages sent to:: {} for level {}".format(dst, i))
        else:
          log.debug("Sending rdv query messages")

          self.numOfVIRO_RDV_QUERY = self.numOfVIRO_RDV_QUERY + 1
          logging.info("VIRO_RDV_QUERY " + str(self.numOfVIRO_RDV_QUERY) + " " + str(time.time()) + " S")

          dst = myvid.getRendezvousID(i)
          pkt = pktFactory.rdvQuery(myvid, dst, i)              
          self.routeViroPacket(pkt)

          log.debug("RDV query message sent to:: {} for level {}".format(dst, i))
      else:      
        log.debug("Sending rdv query messages")

        self.numOfVIRO_RDV_QUERY = self.numOfVIRO_RDV_QUERY + 1
        logging.info("VIRO_RDV_QUERY " + str(self.numOfVIRO_RDV_QUERY) + " " + str(time.time()) + " S")
        
        dst = myvid.getRendezvousID(i)
        pkt = pktFactory.rdvQuery(myvid, dst, i)              
        self.routeViroPacket(pkt)
  
        log.debug("RDV query message sent to:: {} for level {}".format(dst, i))
  
  
  
  
  
    
def launch ():
  core.registerNew(LocalViro)


