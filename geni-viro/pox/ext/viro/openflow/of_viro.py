from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.openflow.libopenflow_01 import _PAD, _PAD2, _PAD3, _PAD4, _PAD6
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.util import str_to_bool
from pox.lib.util import initHelper
from struct import pack

from viro.packet.vid import VidAddr

log = core.getLogger()

VIRO_VENDOR_ID = 0x00002323

def _init_viro_actions():
  viro_actions = [
    "VIRO_AST_PUSH_FD",
    "VIRO_AST_POP_FD",
  
    "VIRO_AST_SET_VID_SW_FD",
    "VIRO_AST_SET_VID_SW_SRC",
    "VIRO_AST_SET_VID_SW_DST",

    "VIRO_AST_SET_VID_HOST_FD",
    "VIRO_AST_SET_VID_HOST_SRC",
    "VIRO_AST_SET_VID_HOST_DST"
  ]
  
  for i, name in enumerate(viro_actions):
    globals()[name] = i

_init_viro_actions()    
  

class viro_action_push_fd(of.ofp_action_vendor_base):
    
  def _init(self, kw):
    self.vendor = VIRO_VENDOR_ID
    self.subtype = VIRO_AST_PUSH_FD
    self.fd = kw['fd']

  def _body_length(self):
    return 8
  
  def _pack_body (self):
    p = pack("!HHI", self.subtype, self.fd.host, self.fd.sw)
    return p

  def _unpack_body (self, raw, offset, avail):
    offset, (self.subtype, host, sw) = of._unpack('!HHI', raw, offset)
    offset = of._skip(raw, offset, 8)
    
    self.fd = VidAddr(sw, host)
    
    return offset

  def _eq (self, other):
    if self.subtype != other.subtype: return False
    if self.fd != other.fd: return False
    return True

  def _show (self, prefix):
    s = ''
    s += prefix + ('subtype: %d\n' % (self.subtype,))
    s += prefix + ('sw: %d\n' % (self.fd.sw,))
    s += prefix + ('host: %d\n' % (self.fd.host,))
    return s
  
class viro_action_pop_fd(of.ofp_action_vendor_base):
    
  def _init(self, kw):
    self.vendor = VIRO_VENDOR_ID
    self.subtype = VIRO_AST_POP_FD

  def _body_length(self):
    return 8
  
  def _pack_body (self):
    p = pack("!H", self.subtype) + _PAD6
    return p

  def _unpack_body (self, raw, offset, avail):
    offset, (self.subtype,) = of._unpack('!H', raw, offset)
    offset = of._skip(raw, offset, 8)
        
    return offset

  def _eq (self, other):
    if self.subtype != other.subtype: return False
    return True

  def _show (self, prefix):
    s = prefix + ('subtype: %d\n' % (self.subtype,))
    return s


class viro_action_vid_sw(of.ofp_action_vendor_base):
  
  @classmethod
  def set_src(cls, sw = None):
    return cls(VIRO_AST_SET_VID_SW_SRC, sw)
  
  @classmethod
  def set_dst(cls, sw = None):
    return cls(VIRO_AST_SET_VID_SW_DST, sw)
  
  @classmethod
  def set_fd(cls, sw = None):
    return cls(VIRO_AST_SET_VID_SW_FD, sw)

  def __init__ (self, subtype = None, sw = None):
    self.vendor = VIRO_VENDOR_ID
    self.subtype = subtype
    self.sw = 0 if sw is None else sw

  def _body_length(self):
    return 8
  
  def _pack_body(self):
    return pack("!H", self.subtype) + _PAD2 + pack("!I", self.sw)

  def _unpack_body(self, raw, offset, avail):
    offset, (self.subtype, _, _, self.sw) = of._unpack('!HBBI', raw, offset)
    offset = of._skip(raw, offset, 8)
        
    return offset

  def _eq(self, other):
    if self.subtype != other.subtype: return False
    if self.sw != other.sw: return False
    return True

  def _show (self, prefix):
    s = ''
    s += prefix + ('subtype: %d\n' % (self.subtype,))
    s += prefix + ('sw: %d\n' % (self.sw,))
    return s


class viro_action_vid_host(of.ofp_action_vendor_base):
  
  @classmethod
  def set_src(cls, host = None):
    return cls(VIRO_AST_SET_VID_HOST_SRC, host)
  
  @classmethod
  def set_dst(cls, host = None):
    return cls(VIRO_AST_SET_VID_HOST_DST, host)
  
  @classmethod
  def set_fd(cls, host = None):
    return cls(VIRO_AST_SET_VID_HOST_FD, host)

  def __init__ (self, subtype = None, host = None):
    self.vendor = VIRO_VENDOR_ID
    self.subtype = subtype
    self.host = 0 if host is None else host

  def _body_length(self):
    return 8
  
  def _pack_body(self):
    return pack("!HH", self.subtype, self.host) + _PAD4

  def _unpack_body(self, raw, offset, avail):
    offset, (self.subtype, self.host) = of._unpack('!HH', raw, offset)
    offset = of._skip(raw, offset, 8)
        
    return offset

  def _eq(self, other):
    if self.subtype != other.subtype: return False
    if self.host != other.host: return False
    return True

  def _show (self, prefix):
    s = ''
    s += prefix + ('subtype: %d\n' % (self.subtype,))
    s += prefix + ('host: %d\n' % (self.host,))
    return s  
  
  
  
