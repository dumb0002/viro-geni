#!/bin/bash

sudo apt-get update
sudo apt-get install libxml2-dev gcc-multilib pkg-config
sudo apt-get install build-essential autoconf automake libtool linux-headers-`uname -r`
sudo apt-get install libgtk2.0-dev llvm llvm-3.3

cd ~/geni-viro/sparse-0.5.0

make clean
make
sudo make install

cd ~/geni-viro/openvswitch/datapath/linux/

sudo rm *.c

sudo rmdir ~/geni-viro/openvswitch/debian/control
sudo mkdir ~/geni-viro/openvswitch/debian/control


cd ~/geni-viro/openvswitch/
sudo ./ovs.sh install
sudo ./ovs.sh start

