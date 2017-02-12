#!/bin/sh


# controllers
ctl_remote=127.0.0.1
port_remote=6633
ctl_local=127.0.0.1
port_local=6634
sw_vid="0000000000000002"


# Add a switch bridge:
sudo ovs-vsctl del-br br0
sudo ovs-vsctl add-br br0
sudo ovs-vsctl list-br



while read line 
do 
    sudo ifconfig $line 0
    sudo ovs-vsctl add-port br0 $line
    sudo ovs-vsctl list-ports br0

done <interfaces.txt



# Set Switch Vid
sudo ovs-vsctl set bridge br0 other-config:datapath-id=$sw_vid
sudo ovs-vsctl get bridge br0 datapath_id



# Set Remote Controller
sudo ovs-vsctl set-controller br0 tcp:$ctl_remote:$port_remote \tcp:$ctl_local:$port_local 

sudo ovs-vsctl set-fail-mode br0 secure

sudo ovs-vsctl show
