from mininet.node import Host
from mininet.util import quietRun

class ViroHost(Host):
  """ A viro host """
  
  def __init__(self, *args, **kwargs):
    Host.__init__(self, *args, **kwargs)
    
  def terminate(self):
    if self._use_dhcp:
      self.cmd('dhclient -r %s-eth0' % self.name)
      
    Host.terminate(self)
    
  def cleanup(self):
    Host.cleanup(self)
    
    if self._detach_screen:
      quietRun('screen -S mininet.%s -X quit' % self.name)
    
  def detachScreen(self):
    if self._detach_screen:
      self.cmd('screen -dmS mininet.' + self.name)

  def dhclient(self):
    if self._use_dhcp:
      self.cmd('dhclient -4 -1 %s-eth0' % self.name)
    
  def disableIPv6(self):
    if self._disable_ipv6:
      self.cmd('sysctl net.ipv6.conf.%s-eth0.disable_ipv6=1' % self.name)
    
  def initViroHost(self):
    """ Initialize the viro host """
    self._use_dhcp = self.params.get('useDHCP')
    self._detach_screen = self.params.get('detachScreen')
    self._disable_ipv6 = self.params.get('disableIPv6')
        
    self.detachScreen()
    self.disableIPv6()
    self.dhclient()
  
  def setMacAddress(self, mac):
      self.setMAC(mac)
