from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.util import str_to_bool
from pox.lib.addresses import IPAddr, EthAddr
from pox.lib.recoco import Timer

from viro.packet.viro import viro
from viro.packet.vid import VidAddr
from struct import pack, unpack

from viro.switch import Switch
from viro.host import Host

from viro.topology import Topology
from viro.local.controller import LocalViro
import viro.factory.message as msgFactory
import viro.factory.packet as pktFactory
import pox.lib.packet as pkt

from viro.packet.viro_ctrl import viroctrl
from viro.packet.viro import viro
import viro.openflow.of_nicira as of_nicira
import pox.openflow.libopenflow_01 as of
import time

import logging
import datetime



log = core.getLogger()



class RemoteViro(EventMixin):
  """ Waits for OpenFlow switches to connect and makes them viro switches.
  This module is supposed to be the management plane for viro """
  
  _core_name = "viro_remote"
  
  CONTROLLER_ID = 1

  # Nov.2015 Count of control packets
  numOfARP_REQUEST = 0
  numOfDHCP_REQUEST = 0
  numOfVIRO_VID_REQUEST = 0
  numofVIRO_HOST_WITHDRAW = 0
  numOfVIRO_CONTROLLER_ECHO = 0
  numOfVIRO_LOCAL_HOST = 0



  def __init__ (self):
    """ Listen to events from viro_switch and viro_dhcp modules """
    EventMixin.__init__(self)
    self.listenTo(core.viro_core)
    self.listenTo(core.viro_dhcpd)
    self.listenTo(core.viro_arpd)
    
    self.topo = Topology()
    
    Timer(5, self._viro_remote_controller_echo, recurring=True)    

  def _handle_ViroSwitchUp(self, event):
    """ Register a viro switch to the remote controller """
    log.debug("Connection %s %s" % (event.connection, dpidToStr(event.dpid)))
    
    # register the viro switch
    vid = VidAddr(event.dpid, 0x00)

    sw = self.topo.addSwitch(Switch(event.dpid, vid, event.connection))
    
    # set the remote controller id at the switch    
    sw.connection.send(msgFactory.ofpControllerId(RemoteViro.CONTROLLER_ID))
    
    # enable the flowMod tableId extension (nicira extensions)
    sw.connection.send(msgFactory.ofpFlowModTableId())
    
    # fm = of_nicira.nx_flow_mod()
    # fm.match.eth_type = viro.VIRO_TYPE
    # fm.match.viro_dst_sw = 0x22220000 
    # fm.match.viro_dst_sw_mask = 0xffff0000
    # fm.match.viro_src_host = 0xabcd
    # fm.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
    # sw.connection.send(fm)
    
      
  def _handle_ARPRequest(self, event):
    """ First check if the host is newly attached to another switch"""
    # Nov.2015
    self.numOfARP_REQUEST = self.numOfARP_REQUEST + 1
    logging.info("ARP " + str(self.numOfARP_REQUEST) + " " + str(time.time()) + " R")
    

    #log.info("Event.DPID {}".format(event.dpid))
    #log.info("Event.SRC {}".format(event.ip))
    #log.info("Event.MAC {}".format(self.topo.findHostByIp(event.ip).mac))
    #log.info("Event.DST {}".format(event.dst))
    #log.info("Event.PORT {}".format(event.port))

    compareHost = self.topo.findHostByIp(event.ip)
    if compareHost is not None:
      compareSwitch = self.topo.findSwitchByDpid(event.dpid)
      if compareSwitch.vid.sw != compareHost.vid.sw:
        # Delete Original
        oldSwitch = self.topo.findSwitchByVid(VidAddr(compareHost.vid.sw, 0x00))
        self.topo.deleteHost(compareHost)
        oldSwitch.deleteHost(compareHost)

        # Add new
        newVID = VidAddr(compareSwitch.vid.sw, compareSwitch.nextHostId())
        newHost = self.topo.addHost(Host(compareHost.mac, event.ip, newVID, event.port, compareSwitch))
        compareSwitch.addHost(newHost)

        # Notify local controller
        self.numOfVIRO_LOCAL_HOST = self.numOfVIRO_LOCAL_HOST+ 1
        logging.info("LOCAL_HOST " + str(self.numOfVIRO_LOCAL_HOST) + " " + str(time.time()) + " S")

        self.send_local_host(compareHost.mac, event.ip, newVID, event.port, compareSwitch)


    if event.dst == IPAddr("192.168.0.254"):
      event.reply = EthAddr("11-22-33-44-55-66")
      return

    """ Update the reply field in the ARP request """        
    host = self.topo.findHostByIp(event.dst) # matching on the destination IP Address

     # check if src and dst hosts are attached to the same switch. If so return the "true" MAC address for the dst
    if host:
       if host.vid.sw == compareHost.vid.sw:
          log.debug("Hosts attached to the same switch src-mac=%s dst-mac=%s", host.mac, compareHost.mac)
          event.reply = EthAddr(host.mac.raw)

       else:
           event.reply = EthAddr(host.vid.raw)
    else:
      log.debug("Host not found in _handle_ARPRequest")
    
    
    
  def _handle_DHCPLease(self, event):
    """ Register a host """
    # Nov.2015
    self.numOfDHCP_REQUEST = self.numOfDHCP_REQUEST + 1
    logging.info("DHCP " + str(self.numOfDHCP_REQUEST) + " " + str(time.time()) + " R")

    log.debug("handling dhcp lease event dpid=%s mac=%s ip=%s", dpidToStr(event.dpid), event.host_mac, event.ip)
    
    sw = self.topo.findSwitchByDpid(event.dpid)
    hostMac = event.host_mac
    hostIp = event.ip
    hostPort = event.port
    hostVid = VidAddr(sw.vid.sw, sw.nextHostId())
    host = self.topo.addHost(Host(hostMac, hostIp, hostVid, hostPort, sw))
    sw.addHost(host)
        

    self.numOfVIRO_LOCAL_HOST = self.numOfVIRO_LOCAL_HOST+ 1
    logging.info("LOCAL_HOST " + str(self.numOfVIRO_LOCAL_HOST) + " " + str(time.time()) + " S")

    # sending host information to the local controller
    self.send_local_host(hostMac, hostIp, hostVid, hostPort, sw)

 
  def _viro_remote_controller_echo(self):
    for sw in self.topo.switches():
      packet = pktFactory.controllerEcho(RemoteViro.CONTROLLER_ID, LocalViro.CONTROLLER_ID, sw.vid)
      msg = msgFactory.controllerEcho(LocalViro.CONTROLLER_ID, packet)
      sw.connection.send(msg)
      
      self.numOfVIRO_CONTROLLER_ECHO = self.numOfVIRO_CONTROLLER_ECHO + 1
      logging.info("VIRO_CONTROLLER_ECHO " + str(self.numOfVIRO_CONTROLLER_ECHO) + " " + str(time.time()) + " S")

    log.debug("echo message sent")


  def send_local_host(self, mac, ip, vid, port, sw):
      packet = pktFactory.localhost(mac, ip, port, vid)
      msg = msgFactory.controllerEcho(LocalViro.CONTROLLER_ID, packet)
      sw.connection.send(msg)

      log.debug("local host message sent")


  def _handle_ViroPacketInVIROCtrl(self, event):
    """ VIRO control Vid Request pkts """
    
    viropkt = event.packet
    inport = event.port
   
    log.debug(str(viropkt))

    ctrlpkt = viropkt.payload

    if ctrlpkt.op == viroctrl.VID_REQUEST:
       # local control vid request message
       # assigns the VidAddress the the local host attached to sw
       self.numOfVIRO_VID_REQUEST = self.numOfVIRO_VID_REQUEST + 1
       logging.info("VIRO_VID_REQUEST " + str(self.numOfVIRO_VID_REQUEST) + " " + str(time.time()) + " R")

       log.debug('Receiving VidRequest pkt from local controller')
       payload = ctrlpkt.payload
       mac  = payload.mac
       ip = payload.ip
       port = payload.port

       sw = self.topo.findSwitchByDpid(event.dpid)
       vid = VidAddr(sw.vid.sw, sw.nextHostId())
       host = self.topo.addHost(Host(mac, ip, vid, port, sw))
       sw.addHost(host)
     
       # sending host information to the local controller
       self.send_local_host(mac, ip, vid, port, sw)

    elif ctrlpkt.op == viroctrl.HOST_WITHDRAW:
      self.numOfVIRO_HOST_WITHDRAW = self.numOfVIRO_HOST_WITHDRAW + 1
      logging.info("VIRO_HOST_WITHDRAW " + str(self.numOfVIRO_HOST_WITHDRAW) + " " + str(time.time()) + " R")

      log.debug('Receiving a failed host packet')
      host_ip = ctrlpkt.payload.failed_host
       
      log.debug('Updating its global topology table')
      self.topo.deleteHostByIP(host_ip) # remove host


def start():
  core.registerNew(RemoteViro)
  
def launch():
  core.call_when_ready(start, ['viro_dhcpd', 'viro_core', 'viro_arpd'])

