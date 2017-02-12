
class Host(object):
  
  
  _ips = {}
  _vids = {}
  _macs = {}
  
  def __init__(self, mac, ip, vid, port, sw):
    """ Initialize the viro host object
    mac      host mac address, EthAddr object
    ip       host ip address assigned using dhcp, IPAddr object
    vid      host viro vid, VidAddr object
    port     host port connect to the switch, an integer
    sw       the viro switch object that this host is attached to 
    """
    self.mac = mac
    self.ip = ip
    self.vid = vid
    self.port = port
    self.sw = sw
    
    

  
