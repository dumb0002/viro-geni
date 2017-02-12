#!/bin/bash

alias vsctl="sudo ovs-vsctl "
alias ofctl="sudo ovs-ofctl "
alias dpctl="sudo ovs-dpctl "
alias appctl="sudo ovs-appctl "
alias oftrace="sudo ovs-appctl ofproto/trace "
alias lflows="ofctl dump-flows "
alias dflows="ofctl del-flows "

#alias ovs="sudo $HOME/geni-viro/openvswitch/ovs.sh "
#alias ovs-suspend="ovs suspend"
#alias ovs-resume="ovs resume"
#alias ovs-install="ovs install"
#alias ovs-stop="ovs stop"
#alias ovs-uninstall="ovs uninstall"
