import pox.openflow.nicira as nx
from pox.openflow.libopenflow_01 import _PAD6
import pox.openflow.libopenflow_01 as of
from struct import pack, unpack


# send packetIn to a specific controller
nx_action_controller = nx.nx_action_controller

# enables the flowMod tableId extension
nx_flow_mod_table_id = nx.nx_flow_mod_table_id

# a flowMod message that uses nx_match
nx_flow_mod = nx.nx_flow_mod

# resubmit
nx_action_resubmit = nx.nx_action_resubmit


# add viro matching extensions
nx._make_nxm_w('NXM_VIRO_DST_SW', 2, 1, 4)
nx._make_nxm('NXM_VIRO_DST_HOST', 2, 2, 2)
nx._make_nxm_w('NXM_VIRO_SRC_SW', 2, 3, 4)
nx._make_nxm('NXM_VIRO_SRC_HOST', 2, 4, 2)
nx._make_nxm_w('NXM_VIRO_FD_SW', 2, 5, 4)
nx._make_nxm('NXM_VIRO_FD_HOST', 2, 6, 2)


class nx_controller_id(nx.nicira_base):

  subtype = nx.NXT_SET_CONTROLLER_ID
  _MIN_LENGTH = 16 + 8

  def _init(self, kw):
    self.controller_id = 0

  def _eq(self, other):
    return self.controller_id == other.controller_id

  def _pack_body(self):
    return _PAD6 + pack("!H", self.controller_id)
  
  def _body_length(self):
    return 8

  def _unpack_body(self, raw, offset, avail):
    offset, (self.controller_id,) = of._unpack("!I", raw, offset)
    return offset

  def _show(self, prefix):
    s = prefix + "controller_id: " + str(self.controller_id) + "\n"
    return s
  
  