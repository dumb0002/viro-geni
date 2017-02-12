# Copyright 2012 James McCauley
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
A quick-and-dirty learning switch for Open vSwitch

This learning switch requires Nicira extensions as found in Open vSwitch.
Furthermore, you must enable packet-in conversion.  Run with something like:
  ./pox.py openflow.nicira --convert-packet-in forwarding.l2_nx

This forwards based on ethernet source and destination addresses.  Where
l2_pairs installs rules for each pair of source and destination address,
this component uses two tables on the switch -- one for source addresses
and one for destination addresses.  Specifically, we use tables 0 and 1
on the switch to implement the following logic:
0. Is this source address known?
   NO: Send to controller (so we can learn it)
1. Is this destination address known?
   YES:  Forward out correct port
   NO: Flood

Note that unlike the other learning switches *we keep no state in the
controller*.  In truth, we could implement this whole thing using OVS's
learn action, but doing it something like is done here will still allow
us to implement access control or something at the controller.
"""

from pox.core import core
from pox.lib.addresses import EthAddr
import pox.openflow.libopenflow_01 as of
import pox.openflow.nicira as nx
from pox.lib.revent import EventRemove

import viro.openflow.of_nicira as vnx
from viro.packet.vid import VidAddr
from viro.packet.viro import viro
import viro.openflow.of_viro as vof
from pox.lib.packet.ethernet import ethernet

# Even a simple usage of the logger is much nicer than print!
log = core.getLogger()


def _handle_ConnectionUp (event):

  # Turn on ability to specify table in flow_mods
  # msg = nx.nx_flow_mod_table_id()
  # event.connection.send(msg)

  # Clear second table
  # msg = nx.nx_flow_mod(command=of.OFPFC_DELETE, table_id = 1)
  # event.connection.send(msg)

  # Fallthrough rule for table 0: flood and send to controller
  # msg = nx.nx_flow_mod()
  # msg.priority = 1 # Low priority
  # msg.actions.append(of.ofp_action_dl_addr.set_dst(EthAddr("11-22-33-44-55-66")))
  # msg.actions.append(of.ofp_action_output(port = of.OFPP_CONTROLLER))
  # msg.actions.append(nx.nx_action_resubmit.resubmit_table(table = 1))
  # event.connection.send(msg)

  # src_vid = VidAddr(0x04, 0x01)
  # dst_vid = VidAddr(0x07, 0x01)

  msg = vnx.nx_flow_mod()
  msg.match.in_port = 1
  msg.actions.append(vof.viro_action_push_fd(fd = VidAddr(0x08, 0x0a)))
  msg.actions.append(of.ofp_action_output(port = 2))
  event.connection.send(msg)

  msg = vnx.nx_flow_mod()
  msg.match.in_port = 2
  msg.actions.append(vof.viro_action_pop_fd())
  msg.actions.append(of.ofp_action_output(port = 1))
  event.connection.send(msg)



  # Fallthrough rule for table 1: flood
  # msg = nx.nx_flow_mod()
  # msg.table_id = 1
  # msg.match.eth_type = ethernet.ARP_TYPE
  # msg.match.viro_dst_sw = dst_vid.sw
  # msg.match.viro_dst_sw_mask = 0xffffffff
  # msg.match.eth_dst = "00-00-00-07-00-01"
  #msg.match.eth_dst_mask = "FF-FF-FF-FF-00-00"

  # msg.actions.append(of.ofp_action_output(port = of.OFPP_FLOOD))
  # event.connection.send(msg)


def launch ():
  core.openflow.addListenerByName("ConnectionUp", _handle_ConnectionUp)
